'''
    Compute the walking distance from origin to boarding and from alight to destination
'''
from sys import argv
import pandas as pd
import geopandas as gpd
import zipfile
import urllib2
import json
import csv

from shapely.geometry import LineString

positions_origin_destination_path = argv[1]
passenger_subway_route_path = argv[2]
gtfs_zip_folder = argv[3]

url_head = 'http://router.project-osrm.org/route/v1/driving/'
url_tail = '?alternatives=false&steps=false&geometries=geojson'

def read_file_in_zip(gtfs_zip_folder, file_name):
    zip_file = zipfile.ZipFile(gtfs_zip_folder)
    df_csv = pd.read_csv(zip_file.open(file_name))
    return df_csv

# read passenger origin destination positions
df_od_positions = pd.read_csv(positions_origin_destination_path)
# select those made by subway
df_od_positions = df_od_positions[df_od_positions['MODE_G10'] == 1]

# read passenger subway route
df_sbwy_routes = pd.read_csv(passenger_subway_route_path)

# get station positions
df_stop_postions = read_file_in_zip(gtfs_zip_folder, 'stops.txt')

for index, trip in df_sbwy_routes.iterrows():
    # get origin destination positions
    sampn_perno_tripno = trip['sampn_perno_tripno']
    sampn_perno_tripno = sampn_perno_tripno.split('_')
    od_positions = df_od_positions[(df_od_positions['sampn'] == int(sampn_perno_tripno[0]))\
    & (df_od_positions['perno'] == int(sampn_perno_tripno[1]))\
    & (df_od_positions['tripno'] == int(sampn_perno_tripno[2]))]

    # get boarding alighting postions
    boarding_position = df_stop_postions[df_stop_postions['stop_id'] == trip['boarding_stop_id']]
    alighting_position = df_stop_postions[df_stop_postions['stop_id'] == trip['alighting_stop_id']]

    

# request route, distance and durantion
#   from origin to boarding station
#   from alighting station to destination
# save route and distance
