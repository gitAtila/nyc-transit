'''
    Reconstruct routes using OpenTripPlanner just for specific modes
'''

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
# mode_names = argv[3] 	# TRANSIT, CAR, BUS, WALK and/or SUBWAY (separated by comma)
# mode_codes = argv[4]	# 1 NYC Subway Only
						# 2 NYC Subway + Bus
						# 3 NY or MTA Bus (no sub)
						# 4 Commuter Rail (no nyct)l
						# 5 Other Rail (no nyct)
						# 6 Other Transit (no nyct)
						# 7 Taxi, Car/Van Service
						# 8 Auto Driver/Passenger
						# 9 Walk (bike)
						# 10 At-Home/Refused
gtfs_year = int(argv[3])
router_id = argv[4]
original_modes = map(int, argv[5].split(','))
route_mode = int(argv[6])
# print modes_origin
# stop

equivalence_survey_otp_modes = {1:'SUBWAY,WALK', 2:'TRANSIT,WALK', 3:'BUS,WALK', 7:'CAR', 8:'CAR', 9:'WALK'}

def equivalent_weekday(original_date_time, new_date_time):
    if original_date_time.weekday() == new_date_time.weekday():
        return new_date_time

    day_before = new_date_time
    day_after = new_date_time
    while day_before.weekday() != original_date_time.weekday()\
    and day_after.weekday() != original_date_time.weekday():
        day_after += timedelta(days=1)
        day_before -= timedelta(days=1)

    if day_before.weekday() == original_date_time.weekday():
        return day_before
    else:
        return day_after

def trip_route_otp(df_trips, original_modes, trip_mode, gtfs_year, router_id, result_file):
	total_trips = len(df_trips)

	list_passengers_trip = []
	otp = OTP_routing(router_id)

	for index, trip in df_trips.iterrows():
		total_trips -= 1
		print 'total_trips', total_trips

		sampn_perno_tripno = str(trip['sampn']) + '_' + str(trip['perno'])\
		+ '_' + str(trip['tripno'])
		print '\n', sampn_perno_tripno

		# if sampn_perno_tripno != '6049554_1_1': continue

		date_time_origin = trip['date_time_origin']
		print 'date_time_origin', date_time_origin

		if pd.isnull(date_time_origin) == False:
			# find equivalent day in the GTFS's year
			gtfs_day = datetime(gtfs_year, date_time_origin.month, date_time_origin.day)
			new_day = equivalent_weekday(date_time_origin, gtfs_day)

			# while gtfs_day.weekday() != date_time_origin.weekday():
			# 	gtfs_day += timedelta(days=1)

			new_date_time_origin = datetime.combine(new_day.date(), date_time_origin.time())
			print 'new_date_time_origin', new_date_time_origin

			print trip['lon_origin'], trip['lat_origin']

			# origin position were informed
			if math.isnan(trip['lon_origin']) == False and math.isnan(trip['lon_destination']) == False:
				if trip['MODE_G10'] not in original_modes: continue

				# trip_mode =  equivalence_survey_otp_modes[trip['MODE_G10']]
				print trip['MODE_G10'], trip_mode
				# print date, time
				try:
					passenger_otp_trip = otp.route_positions(trip['lat_origin'], trip['lon_origin'],\
					trip['lat_destination'], trip['lon_destination'], trip_mode, new_date_time_origin)
				except: # mode unknown
					passenger_otp_trip = []

				for passenger_trip in passenger_otp_trip:
					if len(passenger_trip) > 0:
						passenger_trip['sampn_perno_tripno'] = sampn_perno_tripno

						if trip['MODE_G10'] == 7:
							passenger_trip['mode'] = 'TAXI'

						list_passengers_trip.append(passenger_trip)

	df_passenger_trip = pd.DataFrame(list_passengers_trip)
	print df_passenger_trip
	df_passenger_trip = df_passenger_trip[['sampn_perno_tripno', 'mode', 'trip_sequence',\
	'pos_sequence','date_time', 'longitude', 'latitude', 'distance', 'stop_id']]
	print df_passenger_trip
	df_passenger_trip.to_csv(result_file, index_label='id')

df_trips = pd.read_csv(source_trips_path)
# df_trips = df_trips.head(100)
# if ',' in mode_codes:
# 	mode_codes = [int(code) for code in mode_codes.split(',')]
# else:
# 	mode_codes = [int(mode_codes)]
# print mode_codes
# print df_trips['MODE_G10'].unique()
# print original_modes
df_trips = df_trips[df_trips['MODE_G10'].isin(original_modes)]
df_trips['date_time_origin'] = pd.to_datetime(df_trips['date_time_origin'])
df_trips['date_time_destination'] = pd.to_datetime(df_trips['date_time_destination'])

trip_route_otp(df_trips, original_modes, equivalence_survey_otp_modes[route_mode], gtfs_year, router_id, result_file)
