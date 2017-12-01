# find transit passenger route
from sys import argv, path, maxint
import os
path.insert(0, os.path.abspath("../map_routing"))
from datetime import datetime, timedelta

import pandas as pd
import math

from otp_routing import OTP_routing

survey_trips_path = argv[1]
# equivalence_survey_gtfs_path = argv[2]
# day_type = argv[3]
result_file = argv[2]

def float_to_int_str(float_number):
	return str(float_number).split('.')[0]

def subway_trips_gtfs(df_trips, result_file, gtfs_year, router_id):

	list_subway_passengers_trip = []

	otp = OTP_routing('nyc')

	# select subway trips
	df_subway_trips = df_trips[df_trips['MODE_G10'] == 1]
	df_subway_trips = df_subway_trips.dropna(subset=['StopAreaNo','date_time_origin','lon_destination','lat_destination'])
	df_subway_trips['date_time_origin'] = pd.to_datetime(df_subway_trips['date_time_origin'])

	for index, sbwy_trip in df_subway_trips.iterrows():

		sampn_perno_tripno = str(sbwy_trip['sampn']) + '_' + str(sbwy_trip['perno'])\
		+ '_' + str(sbwy_trip['tripno'])

		date_time_origin = sbwy_trip['date_time_origin']
		print 'date_time_origin', date_time_origin

		# find equivalent day in the GTFS's year
		gtfs_day = datetime(gtfs_year, date_time_origin.month, 1)
		while gtfs_day.weekday() != date_time_origin.weekday():
			gtfs_day += timedelta(days=1)

		new_date_time_origin = datetime.combine(gtfs_day.date(), date_time_origin.time())
		print 'new_date_time_origin', new_date_time_origin

		print sbwy_trip['lon_origin'], sbwy_trip['lat_origin']

		# origin position were informed
		if math.isnan(sbwy_trip['lon_origin']) == False and math.isnan(sbwy_trip['lon_destination']) == False:
			date = new_date_time_origin.strftime('%m-%d-%Y')
			time = new_date_time_origin.strftime('%I:%M%p')

			# print date, time
			passenger_transit_trip = otp.route_positions(sbwy_trip['lat_origin'], sbwy_trip['lon_origin'],\
			sbwy_trip['lat_destination'], sbwy_trip['lon_destination'], 'SUBWAY,WALK', date, time)

			for passenger_trip in passenger_transit_trip:
				if len(passenger_trip) > 0:
					passenger_trip['sampn_perno_tripno'] = sampn_perno_tripno
					correct_date = date_time_origin.date()
					if passenger_trip['date_time'].date() > new_date_time_origin.date():
						difference_days = (passenger_trip['date_time'] - new_date_time_origin).days
						correct_date = correct_date + timedelta(days=difference_days)
					correct_date_time = datetime.combine(correct_date, passenger_trip['date_time'].time())
					passenger_trip['date_time'] = correct_date_time
					list_subway_passengers_trip.append(passenger_trip)
					# print passenger_trip

			print ''
			# break
	df_subway_passenger_trip = pd.DataFrame(list_subway_passengers_trip)
	df_subway_passenger_trip = df_subway_passenger_trip[['sampn_perno_tripno','trip_sequence',\
	'pos_sequence','date_time', 'longitude', 'latitude', 'distance', 'stop_id']]
	print df_subway_passenger_trip
	df_subway_passenger_trip.to_csv(result_file, index_label='id')

df_trips = pd.read_csv(survey_trips_path)
# df_equivalence_survey_gtfs = pd.read_csv(equivalence_survey_gtfs_path)

subway_trips_gtfs(df_trips, result_file, 2010, 'nyc')
