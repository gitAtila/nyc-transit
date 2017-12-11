# find transit passenger route
from sys import argv, path, maxint
# import os
# path.insert(0, os.path.abspath("../map_routing"))
from datetime import datetime, timedelta

import pandas as pd
import math

from otp_routing import OTP_routing

source_trips_path = argv[1]
result_file = argv[2]
mode_names = argv[3] 	# TRANSIT, CAR, BUS, WALK and/or SUBWAY (separated by comma)
mode_codes = argv[4]	# 1 NYC Subway Only
						# 2 NYC Subway + Bus
						# 3 NY or MTA Bus (no sub)
						# 4 Commuter Rail (no nyct)l
						# 5 Other Rail (no nyct)
						# 6 Other Transit (no nyct)
						# 7 Taxi, Car/Van Service
						# 8 Auto Driver/Passenger
						# 9 Walk (bike)
						# 10 At-Home/Refused
gtfs_year = int(argv[5])
router_id = argv[6]

def trip_route_otp(df_trips, modes, gtfs_year, router_id, result_file):

	list_passengers_trip = []
	otp = OTP_routing(router_id)

	for index, trip in df_trips.iterrows():

		sampn_perno_tripno = str(trip['sampn']) + '_' + str(trip['perno'])\
		+ '_' + str(trip['tripno'])

		date_time_origin = trip['date_time_origin']
		print 'date_time_origin', date_time_origin

		if pd.isnull(date_time_origin) == False:
			# find equivalent day in the GTFS's year
			gtfs_day = datetime(gtfs_year, date_time_origin.month, date_time_origin.day)
			while gtfs_day.weekday() != date_time_origin.weekday():
				gtfs_day += timedelta(days=1)

			new_date_time_origin = datetime.combine(gtfs_day.date(), date_time_origin.time())
			print 'new_date_time_origin', new_date_time_origin

			print trip['lon_origin'], trip['lat_origin']

			# origin position were informed
			if math.isnan(trip['lon_origin']) == False and math.isnan(trip['lon_destination']) == False:

				# print date, time
				passenger_otp_trip = otp.route_positions(trip['lat_origin'], trip['lon_origin'],\
				trip['lat_destination'], trip['lon_destination'], modes, new_date_time_origin)

				for passenger_trip in passenger_otp_trip:
					if len(passenger_trip) > 0:
						passenger_trip['sampn_perno_tripno'] = sampn_perno_tripno
						list_passengers_trip.append(passenger_trip)

	df_passenger_trip = pd.DataFrame(list_passengers_trip)
	df_passenger_trip = df_passenger_trip[['sampn_perno_tripno','trip_sequence',\
	'pos_sequence','date_time', 'longitude', 'latitude', 'distance', 'stop_id']]
	print df_passenger_trip
	df_passenger_trip.to_csv(result_file, index_label='id')

df_trips = pd.read_csv(source_trips_path)
if ',' in mode_codes:
	mode_codes = [int(code) for code in mode_codes.split(',')]
else:
	mode_codes = [int(mode_codes)]
print mode_codes
df_trips = df_trips[df_trips['MODE_G10'].isin(mode_codes)]
df_trips['date_time_origin'] = pd.to_datetime(df_trips['date_time_origin'])
df_trips['date_time_destination'] = pd.to_datetime(df_trips['date_time_destination'])

trip_route_otp(df_trips, mode_names, gtfs_year, router_id, result_file)
