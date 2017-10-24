# find transit passenger route
from sys import argv
import pandas as pd
import math
import geopandas as gpd

import matplotlib.pyplot as plt
import transit_graph

shapefile_census_tract_base_path = argv[1]
shapefile_stations = argv[2]

survey_trips = argv[3]
survey_stations = argv[4]

equivalence_survey_shapefile = argv[5]

results_folder = argv[6]

def df_from_csv(survey_trips):
	return pd.read_csv(survey_trips)

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
df_trips = df_from_csv(survey_trips)
df_survey_stations = df_from_csv(survey_stations)
df_equivalence_survey_shapefile = df_from_csv(equivalence_survey_shapefile)
# shapefiles
gdf_subway_stations = gpd.GeoDataFrame.from_file(shapefile_stations)
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

df_trips_in_nyc = get_transit_trips_in_nyc(df_trips, gdf_census_tract)

'''
	Find out the subway passenger trip route
'''

borough_survey_shape = {1:'1', 2:'4', 3:'2', 4:'3', 5:'5'}
list_stations = []

# select trips by subway
df_subway_trips = df_trips_in_nyc[df_trips_in_nyc['MODE_G10'] == 1]
for index, sbwy_trip in df_subway_trips.iterrows():

	# get interested variables
	trip_id = str(sbwy_trip['sampn']) + '_' + str(sbwy_trip['perno']) + '_' + str(sbwy_trip['tripno'])
	print 'trip_id', trip_id

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
		shapefile_station_id = df_equivalence_survey_shapefile[df_equivalence_survey_shapefile['sv_id'] == float(sbwy_station_id)]['sf_id']
		gdf_boarding_station = gdf_subway_stations[gdf_subway_stations['objectid'] == shapefile_station_id.iloc[0]]
	else:
		print 'There is not information of boarding station'
		sbwy_boarding_station_name = ''
		sf_boarding_station_name = ''

	print 'sbwy_station_id', sbwy_station_id
	print 'sbwy_boarding_station_name', sbwy_boarding_station_name
	print 'sf_boarding_station', gdf_boarding_station['objectid'].iloc[0], gdf_boarding_station['name'].iloc[0], gdf_boarding_station['line'].iloc[0]
	#list_stations.append(sbwy_station_id)
	print ''

	# get census tract of origin and census tract of destination
	try:
		gdf_ct_origin = gdf_census_tract[gdf_census_tract['ct2010'] == ct_origin]
		gdf_ct_origin = gdf_ct_origin[gdf_ct_origin['boro_code'] == borough_survey_shape[borough_origin]]

		gdf_ct_destination = gdf_census_tract[gdf_census_tract['ct2010'] == ct_destination]
		gdf_ct_destination = gdf_ct_destination[gdf_ct_destination['boro_code'] == borough_survey_shape[borough_destination]]

		

	except KeyError:
		print 'Census tract out of NYC area'

	# fig, ax = plt.subplots()
	# ax.set_aspect('equal')
	# gdf_census_tract.plot(ax=ax, color='white', linewidth=0.5, edgecolor='0.5')
	# gdf_ct_origin.plot(ax=ax, color='blue', linewidth=0.5, edgecolor='0.5')
	# gdf_ct_destination.plot(ax=ax, color='red', linewidth=0.5, edgecolor='0.5')
	# gdf_boarding_station.plot(ax=ax, color='green', markersize=5)
	# fig.savefig(results_folder + 'test_ct_' + trip_id + '.pdf')

	break

#gdf_census_tract = gpd.read_file(shapefile_census_tract_base_path)
#list_stations.sort()
#print list_stations

df_subway_bus_trips = df_trips_in_nyc[df_trips_in_nyc['MODE_G10'] == 2]
df_bus_trips = df_trips_in_nyc[df_trips_in_nyc['MODE_G10'] == 3]

'''
	Add intermediate stations to passenger's trip
'''
