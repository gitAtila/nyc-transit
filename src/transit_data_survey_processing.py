# find transit passenger route
from sys import argv
import pandas as pd
import math
import geopandas as gpd
import matplotlib.pyplot as plt

import transit_graph as tg
import gtfs_processing as gtfs

shapefile_census_tract_base_path = argv[1]
shapefile_stations_path = argv[2]
shapefile_links_path = argv[3]
survey_trips_path = argv[4]
survey_stations_path = argv[5]
equivalence_survey_shapefile_path = argv[6]
gtfs_path = argv[7]

results_folder = argv[8]

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

	# select trips by subway
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
				# get subway passenger route from graph
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

gtfs_nyc_subway = gtfs.TransitFeedProcessing(gtfs_path)
df_nyc_subway_links = gtfs_nyc_subway.links_between_stations()
print df_nyc_subway_links

df_subway_bus_trips = df_trips_in_nyc[df_trips_in_nyc['MODE_G10'] == 2]
df_bus_trips = df_trips_in_nyc[df_trips_in_nyc['MODE_G10'] == 3]

'''
	Add intermediate stations to passenger's trip
'''
