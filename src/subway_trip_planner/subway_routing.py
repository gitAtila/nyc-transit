# find transit passenger route
from sys import argv
from datetime import datetime

import pandas as pd
import math
import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx

import shape_transit_graph as tg
import gtfs_processing as gp
import gtfs_transit_graph as gtg

survey_trips_path = argv[1]
gtfs_links_path = argv[2]
gtfs_path = argv[3]
equivalence_survey_gtfs_path = argv[4]
trip_times_path = argv[5]
day_type = argv[6]

results_folder = argv[7]

def subway_passenger_trip(sbwy_trip, df_equivalence_survey_gtfs, nyc_transit_graph):

	passenger_transit_trip = []

	# get boarding station in graph
	sbwy_station_id = float_to_int_str(sbwy_trip['StopAreaNo'])
	if sbwy_station_id != '0':
		gtfs_station_id = df_equivalence_survey_gtfs[df_equivalence_survey_gtfs['survey_stop_id']\
		 == float(sbwy_station_id)]['gtfs_stop_id'].iloc[0]
		#df_boarding_station = df_subway_stations[df_subway_stations['stop_id'] == gtfs_station_id]
		print 'gtfs_station_id', gtfs_station_id
		print 'number_subway_routes', sbwy_trip['NSUB']
		number_subway_routes = sbwy_trip['NSUB']
		if number_subway_routes == 0:
			number_subway_routes = 3

		# get subway passenger route through graph
		passenger_transit_trip = nyc_transit_graph.station_location_transfers(gtfs_station_id,\
		(sbwy_trip['lon_destination'], sbwy_trip['lat_destination']), number_subway_routes,\
		sbwy_trip['date_time_origin'])

		for index in range(len(passenger_transit_trip)):
			sampn_perno_tripno = str(sbwy_trip['sampn']) + '_' + str(sbwy_trip['perno'])\
			+ '_' + str(sbwy_trip['tripno'])
			print 'sampn_perno_tripno', sampn_perno_tripno

			passenger_transit_trip[index]['sampn_perno_tripno'] = sampn_perno_tripno
			passenger_transit_trip[index]['trip_sequence'] = index

	else:
		print 'Error: There is not any information about boarding station.'
		print ''
		sf_boarding_station_name = ''

	return passenger_transit_trip

def subway_trips_gtfs(df_trips, gtfs_links_path, gtfs_path, day_type, results_folder,\
 result_file):

	list_subway_passengers_trip = []

	# select subway trips
	df_subway_trips = df_trips[df_trips['MODE_G10'] == 1]
	df_subway_trips = df_subway_trips.dropna(subset=['StopAreaNo','lon_destination','lat_destination'])
	print df_subway_trips
	# load transit_graph
	nyc_transit_graph = gtg.GtfsTransitGraph(gtfs_links_path, gtfs_path, trip_times_path, day_type)

	for index, sbwy_trip in df_subway_trips.iterrows():
		passenger_transit_trip = subway_passenger_trip(sbwy_trip, nyc_transit_graph)

		for passenger_trip in passenger_transit_trip:
			if len(passenger_trip) > 0:
				list_subway_passengers_trip.append(passenger_trip)
				print passenger_trip
		#break
		print ''

	df_subway_passenger_trip = pd.DataFrame(list_subway_passengers_trip)
	df_subway_passenger_trip = df_subway_passenger_trip[['sampn_perno_tripno','trip_sequence','gtfs_trip_id',\
	'boarding_stop_id','alighting_stop_id']]
	df_subway_passenger_trip.to_csv(results_folder + result_file, index_label='id')

def passenger_trip(df_trips, sampn_perno_tripno, day_type):
	sampn_perno_tripno = sampn_perno_tripno.split('_')

	# select subway trips
	df_trips = df_trips[df_trips['sampn'] == int(sampn_perno_tripno[0])]
	df_trips = df_trips[df_trips['perno'] == int(sampn_perno_tripno[1])]
	sbwy_trip = df_trips[df_trips['tripno'] == int(sampn_perno_tripno[2])].iloc[0]
	#print sbwy_trip
	# load transit_graph
	nyc_transit_graph = gtg.GtfsTransitGraph(gtfs_links_path, gtfs_path, trip_times_path, day_type)
	subway_passenger_trip(sbwy_trip, nyc_transit_graph)


df_trips = pd.read_csv(survey_trips_path)
df_equivalence_survey_gtfs = pd.read_csv(equivalence_survey_gtfs_path)

if day_type == 1:
	result_file = 'sbwy_route_wkdy.csv'
elif day_type == 2:
	result_file = 'sbwy_route_sat.csv'
else:
	result_file = 'sbwy_route_sun.csv'

subway_trips_gtfs(df_trips, gtfs_links_path, gtfs_path, day_type, results_folder,result_file)

sampn_perno_tripno = '6043639_1_2'
#passenger_trip(df_trips, sampn_perno_tripno, day_type)
