# find transit passenger route
from sys import argv
import pandas as pd
import math
import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx

import transit_graph as tg
import gtfs_processing as gp

shapefile_census_tract_base_path = argv[1]
shapefile_stations_path = argv[2]
shapefile_links_path = argv[3]
gtfs_links_path = argv[4]
survey_trips_path = argv[5]
survey_stations_path = argv[6]
equivalence_survey_shapefile_path = argv[7]
equivalence_gtfs_shape_stops_path = argv[8]
gtfs_path = argv[9]

results_folder = argv[10]

def df_from_csv(survey_trips_path):
	return pd.read_csv(survey_trips_path)

def float_to_int_str(float_number):
	return str(float_number).split('.')[0]

def get_origin_destination_tract_id(s_trip):
	o_tract_id = float_to_int_str(s_trip['O_TRACT'])
	o_tract_id = o_tract_id[len(float_to_int_str(s_trip['O_COUNTY'])):]

	d_tract_id = float_to_int_str(s_trip['D_TRACT'])
	d_tract_id = d_tract_id[len(float_to_int_str(s_trip['D_COUNTY'])):]

	return {'o_tract_id': o_tract_id, 'd_tract_id': d_tract_id}


'''
	Read transit data
'''
# od survey
df_trips = df_from_csv(survey_trips_path)
df_survey_stations = df_from_csv(survey_stations_path)
df_equivalence_survey_shapefile = df_from_csv(equivalence_survey_shapefile_path)
# shapefiles
gdf_subway_stations = gpd.GeoDataFrame.from_file(shapefile_stations_path)
gdf_census_tract = gpd.read_file(shapefile_census_tract_base_path)
# gtfs
gtfs_nyc_subway = gp.TransitFeedProcessing(gtfs_path)
df_stop_times = gtfs_nyc_subway.get_stop_times()

def links_from_gtfs(gtfs_path):
	gtfs_nyc_subway = gp.TransitFeedProcessing(gtfs_path)
	df_nyc_subway_links = gtfs_nyc_subway.distinct_links_between_stations()

def links_from_gtfs(equivalence_gtfs_shape_stops_path, shapefile_stations_path, shapefile_links_path):
	# merge shape stations with gtfs stations
	list_gtfs_links_distance = []
	gdf_subway_stations = gpd.GeoDataFrame.from_file(shapefile_stations_path)
	df_equivalence_gtfs_shape_stops = df_from_csv(equivalence_gtfs_shape_stops_path)
	del df_equivalence_gtfs_shape_stops['name']

	# geometry links from shape
	nyc_transit_graph = tg.TransitGraph(shapefile_stations_path, shapefile_links_path)

	gdf_shape_links = gpd.GeoDataFrame.from_file(shapefile_links_path)
	df_gtfs_links = df_from_csv(gtfs_links_path)
	# add gtfs stop_id and line on links
	for index, gtfs_link in df_gtfs_links.iterrows():
		line = gtfs_link['route_id']
		gtfs_from_station = gtfs_link['from_parent_station']
		gtfs_to_station = gtfs_link['to_parent_station']
		# get shape id
		shape_from_station = df_equivalence_gtfs_shape_stops[\
		 df_equivalence_gtfs_shape_stops['stop_id'] == gtfs_from_station]['objectid']
		shape_to_station = df_equivalence_gtfs_shape_stops[\
		 df_equivalence_gtfs_shape_stops['stop_id'] == gtfs_to_station]['objectid']

		if len(shape_from_station) == 1 and len(shape_to_station) == 1:
			shape_from_station = shape_from_station.iloc[0]
			shape_to_station = shape_to_station.iloc[0]

			# get distance from path
			geometry = gdf_shape_links.query('(@shape_from_station == node_1 and @shape_to_station == node_2)\
			 or (@shape_from_station == node_2 and @shape_to_station == node_1)')
			if geometry.empty == False:
				path_distance = geometry.iloc[0]['shape_len']
			else:
				try:
					path_distance = nyc_transit_graph.shortest_path_length_line(shape_from_station, shape_to_station, line)
				except:
					path_distance = nyc_transit_graph.shortest_path_length(shape_from_station, shape_to_station)

			dict_gtfs_link_distance = gtfs_link.to_dict()
			dict_gtfs_link_distance['shape_len'] = path_distance
			list_gtfs_links_distance.append(dict_gtfs_link_distance)
		else:
			print 'gtfs_station', gtfs_from_station

	return pd.DataFrame(list_gtfs_links_distance)

'''
	Get trips in New York City
'''
def get_transit_trips_in_nyc(df_trips, gdf_census_tract):
	# select transit trips
	df_transit_trips = df_trips[df_trips['MODE_G2'] == 1]

	list_trips_in_nyc = []
	tract_id_nyc = gdf_census_tract['ct2010'].tolist()
	for index, trip in df_transit_trips.iterrows():
		od_tract = get_origin_destination_tract_id(trip)
		if od_tract['o_tract_id'] in tract_id_nyc and od_tract['d_tract_id'] in tract_id_nyc:
			list_trips_in_nyc.append(trip)

	print 'list_trips_in_nyc', len(list_trips_in_nyc)
	return pd.DataFrame(list_trips_in_nyc)

'''
	Get subway passenger trip route
'''
def subway_trips(df_trips_in_nyc, shapefile_stations_path, shapefile_links_path, results_folder,\
 result_file):

	borough_survey_shape = {1:'1', 2:'4', 3:'2', 4:'3', 5:'5'}
	list_stations = []
	list_bus_route = []

	# select subway trips
	df_subway_trips = df_trips_in_nyc[df_trips_in_nyc['MODE_G10'] == 1]

	# load transit_graph
	nyc_transit_graph = tg.TransitGraph(shapefile_stations_path, shapefile_links_path)

	for index, sbwy_trip in df_subway_trips.iterrows():

		# get interested variables
		sampn_perno_tripno = str(sbwy_trip['sampn']) + '_' + str(sbwy_trip['perno']) + '_' + str(sbwy_trip['tripno'])
		print 'sampn_perno_tripno', sampn_perno_tripno

		# get census tract code from survey
		ct_od = get_origin_destination_tract_id(sbwy_trip)
		ct_origin = ct_od['o_tract_id']
		ct_destination = ct_od['d_tract_id']
		borough_origin = sbwy_trip['O_Boro']
		borough_destination = sbwy_trip['D_Boro']
		nbr_sbwy_segments = sbwy_trip['NSUB']
		list_modes = []

		print 'ct_origin', ct_origin
		print 'ct_destination', ct_destination
		print 'boro_origin', borough_origin
		print 'boro_destination', borough_destination
		print 'nbr_sbwy_segments', nbr_sbwy_segments

		# remove empty mode
		for mode in range(1,17):
			mode_key = 'MODE'
			if math.isnan(sbwy_trip[mode_key + str(mode)]) == False:
				list_modes.append(sbwy_trip[mode_key + str(mode)])
			else:
				break
		print list_modes

		# get boarding station in shapefile
		sbwy_station_id = float_to_int_str(sbwy_trip['StopAreaNo'])
		if math.isnan(float(sbwy_station_id)) == False and sbwy_station_id != '0' and sbwy_station_id != '1384':
			sbwy_boarding_station_name = df_survey_stations[df_survey_stations['Value'] == int(sbwy_station_id)]['Label']
			shapefile_station_id = df_equivalence_survey_shapefile[df_equivalence_survey_shapefile['sv_id'] == float(sbwy_station_id)]['sf_id'].iloc[0]
			gdf_boarding_station = gdf_subway_stations[gdf_subway_stations['objectid'] == shapefile_station_id]
		else:
			print 'There is not information of boarding station'
			sbwy_boarding_station_name = ''
			sf_boarding_station_name = ''

		print 'shapefile_station_id', shapefile_station_id
		print 'sbwy_boarding_station_name', sbwy_boarding_station_name
		print 'sf_boarding_station', gdf_boarding_station['objectid'].iloc[0],\
		 gdf_boarding_station['name'].iloc[0], gdf_boarding_station['line'].iloc[0]

		# get census tract of origin and census tract of destination
		try:
			# discover which was the alight station
			## get the centroid of the census tract
			gdf_ct_destination = gdf_census_tract[gdf_census_tract['ct2010'] == ct_destination]
			gs_ct_destination = gdf_ct_destination[gdf_ct_destination['boro_code'] == borough_survey_shape[borough_destination]]
			destination_centroid = gs_ct_destination.centroid
			#print destination_centroid

			if len(destination_centroid) == 0:
				travel = {'boardings': 0, 'alight_destination_distance': None, 'subway_distance': None}
			else:
				# get subway passenger route through graph
				travel = nyc_transit_graph.station_location_shortest_walk_distance(shapefile_station_id, destination_centroid)
				travel['boardings'] = len(travel['stations'])-1
		        del travel['stations']
		except:
			travel = {'boardings': 0, 'alight_destination_distance': None, 'subway_distance': None}

		travel['sampn_perno_tripno'] = sampn_perno_tripno
		list_bus_route.append(travel)
		print travel
		print ''

	df_bus_routes = pd.DataFrame(list_bus_route)
	print df_bus_routes
	df_bus_routes.to_csv(results_folder + result_file, index_label='id')

df_trips_in_nyc = get_transit_trips_in_nyc(df_trips, gdf_census_tract)
# subway_trips(df_trips_in_nyc, shapefile_stations_path, shapefile_links_path, results_folder,\
#  'sbwy_route_sun.csv')

df_gtfs_links_distance = links_from_gtfs(equivalence_gtfs_shape_stops_path, shapefile_stations_path,\
 shapefile_links_path)

print df_gtfs_links_distance


df_subway_bus_trips = df_trips_in_nyc[df_trips_in_nyc['MODE_G10'] == 2]
df_bus_trips = df_trips_in_nyc[df_trips_in_nyc['MODE_G10'] == 3]

'''
	Add intermediate stations to passenger's trip
'''
