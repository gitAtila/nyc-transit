'''
    Compute the walking distance from origin to boarding and from alight to destination
'''
from sys import argv, path
import os
path.insert(0, os.path.abspath("../map_routing"))

import pandas as pd
import geopandas as gpd
import zipfile
import urllib2
import json
import math
import csv
import osrm_routing as api_osrm
from shapely.geometry import LineString

survey_trips_path = argv[1]
passenger_subway_route_path = argv[2] # empty if not computed
equivalence_survey_gtfs_path = argv[3]
gtfs_zip_folder = argv[4]
result_path = argv[5]

osm = api_osrm.OSRM_routing('walking')

def read_file_in_zip(gtfs_zip_folder, file_name):
    zip_file = zipfile.ZipFile(gtfs_zip_folder)
    df_csv = pd.read_csv(zip_file.open(file_name))
    return df_csv

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
            origin_route = osm.street_routing_steps(trip['lon_origin'], trip['lat_origin'],\
            boarding_position['stop_lon'].iloc[0], boarding_position['stop_lat'].iloc[0])
            for step in origin_route:
                step['sampn_perno_tripno'] = sampn_perno_tripno
                list_origin_route.append(step)

    df_origin_route = pd.DataFrame(list_origin_route)
    df_origin_route = df_origin_route[['sampn_perno_tripno', 'distance','duration','latitude','longitude' ]]
    print df_origin_route
    df_origin_route.to_csv(result_path + 'origin_boarding_walking_route.csv', index_label='id')

def compute_alighting_destination_route(survey_trips_path, passenger_subway_route_path,\
gtfs_zip_folder, result_path):
    # read passenger origin destination positions
    df_od_positions = pd.read_csv(survey_trips_path)
    # select those made by subway
    df_od_positions = df_od_positions[df_od_positions['MODE_G10'] == 1]

    # read passenger subway route
    df_sbwy_routes = pd.read_csv(passenger_subway_route_path)
    # keep just the last trip of each travel
    dict_sbwy_passenger_routes = dict()
    for intex, route in df_sbwy_routes.iterrows():
        dict_sbwy_passenger_routes[route['sampn_perno_tripno']] = route['alighting_stop_id']

    # get station positions
    df_stop_postions = read_file_in_zip(gtfs_zip_folder, 'stops.txt')

    list_origin_route = []
    list_destination_route = []
    for sampn_perno_tripno, alighting_stop_id in dict_sbwy_passenger_routes.iteritems():
        # get origin destination positions
        splitted_sampn_perno_tripno = sampn_perno_tripno.split('_')
        od_positions = df_od_positions[(df_od_positions['sampn'] == int(splitted_sampn_perno_tripno[0]))\
        & (df_od_positions['perno'] == int(splitted_sampn_perno_tripno[1]))\
        & (df_od_positions['tripno'] == int(splitted_sampn_perno_tripno[2]))]

        # get boarding alighting postions
        alighting_position = df_stop_postions[df_stop_postions['stop_id'] == alighting_stop_id]

        print 'alighting_destination'
        destination_route = osm.street_routing_steps(alighting_position['stop_lon'].iloc[0],\
        alighting_position['stop_lat'].iloc[0], od_positions['lon_destination'].iloc[0],\
        od_positions['lat_destination'].iloc[0])
        for step in destination_route:
            step['sampn_perno_tripno'] = sampn_perno_tripno
            list_destination_route.append(step)

    # save route and distance
    df_destination_route = pd.DataFrame(list_destination_route)
    df_destination_route = df_destination_route[['sampn_perno_tripno', 'distance','duration','latitude','longitude' ]]
    print df_destination_route
    df_destination_route.to_csv(result_path + 'alighting_destination_walking_route.csv', index_label='id')

#df_equivalence_survey_gtfs = pd.read_csv(equivalence_survey_gtfs_path)
#compute_origin_boarding_route(survey_trips_path, df_equivalence_survey_gtfs, gtfs_zip_folder, result_path)
compute_alighting_destination_route(survey_trips_path, passenger_subway_route_path, gtfs_zip_folder, result_path)
