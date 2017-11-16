'''
    Compute the walking distance from origin to boarding and from alight to destination
'''
from sys import argv
import pandas as pd
import geopandas as gpd
import zipfile
import urllib2
import json
import math
import csv

from shapely.geometry import LineString

survey_trips_path = argv[1]
passenger_subway_route_path = argv[2] # empty if not computed
equivalence_survey_gtfs_path = argv[3]
gtfs_zip_folder = argv[4]
result_path = argv[5]

def read_file_in_zip(gtfs_zip_folder, file_name):
    zip_file = zipfile.ZipFile(gtfs_zip_folder)
    df_csv = pd.read_csv(zip_file.open(file_name))
    return df_csv

def routing_osrm_api(lon_origin, lat_origin, lon_destination, lat_destination, mode):

    if math.isnan(lon_origin) or math.isnan(lon_destination):
        return {'duration': None, 'distance':None, 'geometry': None}

    url_head = 'http://router.project-osrm.org/route/v1/'
    url_head += mode + '/'
    url_tail = '?alternatives=false&steps=false&geometries=geojson'

    coordinates = str(lon_origin) + ',' + str(lat_origin)\
     + ';' + str(lon_destination) + ',' + str(lat_destination)

    url = url_head + coordinates + url_tail
    print url

    # request from APIs
    # try the url until succeed
    url_error = True
    while url_error == True:
        try:
            route = urllib2.urlopen(url)
            json_route = json.load(route)
            url_error = False

        except urllib2.URLError:
            print 'URLError', len(url)

    if json_route['code'] == 'Ok':
        #print taxi_trip['sampn_perno_tripno']
        geometry = LineString(json_route['routes'][0]['geometry']['coordinates'])
        duration = json_route['routes'][0]['duration']
        distance = json_route['routes'][0]['distance']

        return {'duration': duration, 'distance':distance, 'geometry': geometry}

    return {'duration': None, 'distance':None, 'geometry': None}

def compute_origin_boarding_route(survey_trips_path, df_equivalence_survey_gtfs,\
gtfs_zip_folder, result_path):
    # read passenger origin positions
    df_survey_trips = pd.read_csv(survey_trips_path)
    # select those made by subway
    df_survey_trips = df_survey_trips[df_survey_trips['MODE_G10'] == 1]
    df_survey_trips = df_survey_trips.dropna(subset=['StopAreaNo','lon_origin','lat_origin'])
    # get station positions
    df_stop_postions = read_file_in_zip(gtfs_zip_folder, 'stops.txt')

    df_equivalence_survey_gtfs = pd.read_csv(equivalence_survey_gtfs_path)

    list_origin_route = []
    for index, trip in df_survey_trips.iterrows():
    	sampn_perno_tripno = str(trip['sampn']) + '_' + str(trip['perno'])\
    	+ '_' + str(trip['tripno'])
        print sampn_perno_tripno
        print trip['StopAreaNo']
        # get boarding postions
        if trip['StopAreaNo'] != 0:
            gtfs_station_id = df_equivalence_survey_gtfs[df_equivalence_survey_gtfs['survey_stop_id']\
    		 == float(trip['StopAreaNo'])]['gtfs_stop_id'].iloc[0]
            boarding_position = df_stop_postions[df_stop_postions['stop_id'] == gtfs_station_id]

            print 'origin_boarding'
            #print gdf_destination_route
            origin_route = routing_osrm_api(trip['lon_origin'], trip['lat_origin'],\
            boarding_position['stop_lon'].iloc[0], boarding_position['stop_lat'].iloc[0], 'walking')
            origin_route['sampn_perno_tripno'] = sampn_perno_tripno
            list_origin_route.append(origin_route)
            print origin_route

    gdf_origin_route = gpd.GeoDataFrame(list_origin_route, geometry='geometry')
    print gdf_origin_route
    gdf_origin_route.to_file(result_path + 'origin_boarding_walking_route.shp')

def compute_alighting_destination_route(survey_trips_path, passenger_subway_route_path,\
gtfs_zip_folder, result_path):
    # read passenger origin destination positions
    df_od_positions = pd.read_csv(survey_trips_path)
    # select those made by subway
    df_od_positions = df_od_positions[df_od_positions['MODE_G10'] == 1]

    # read passenger subway route
    df_sbwy_routes = pd.read_csv(passenger_subway_route_path)

    # get station positions
    df_stop_postions = read_file_in_zip(gtfs_zip_folder, 'stops.txt')

    list_origin_route = []
    list_destination_route = []
    for index, trip in df_sbwy_routes.iterrows():
        # get origin destination positions
        sampn_perno_tripno = trip['sampn_perno_tripno']
        sampn_perno_tripno = sampn_perno_tripno.split('_')
        od_positions = df_od_positions[(df_od_positions['sampn'] == int(sampn_perno_tripno[0]))\
        & (df_od_positions['perno'] == int(sampn_perno_tripno[1]))\
        & (df_od_positions['tripno'] == int(sampn_perno_tripno[2]))]

        # get boarding alighting postions
        alighting_position = df_stop_postions[df_stop_postions['stop_id'] == trip['alighting_stop_id']]

        print 'alighting_destination'
        destination_route = routing_osrm_api(alighting_position['stop_lon'].iloc[0], alighting_position['stop_lat'].iloc[0],\
        od_positions['lon_destination'].iloc[0], od_positions['lat_destination'].iloc[0], 'walking')
        print destination_route
        destination_route['sampn_perno_tripno'] = trip['sampn_perno_tripno']
        list_destination_route.append(destination_route)
        print ''
        #break

    # save route and distance
    gdf_destination_route = gpd.GeoDataFrame(list_destination_route, geometry='geometry')
    print gdf_destination_route
    gdf_destination_route.to_file(result_path + 'alighting_destination_walking_route.shp')

#df_equivalence_survey_gtfs = pd.read_csv(equivalence_survey_gtfs_path)
#compute_origin_boarding_route(survey_trips_path, df_equivalence_survey_gtfs, gtfs_zip_folder, result_path)
compute_alighting_destination_route(survey_trips_path, passenger_subway_route_path, gtfs_zip_folder, result_path)
