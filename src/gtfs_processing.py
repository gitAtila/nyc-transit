'''
    Read GTFS file and plot stops and connections
'''

from sys import argv
import os
import zipfile

import pandas as pd

import geopandas as gpd
from shapely.geometry import Point, LineString

import matplotlib.pyplot as plt

gtfs_zip_folder = argv[1]
result_path = argv[2]


def read_file_in_zip(gtfs_zip_folder, file_name):
    zip_file = zipfile.ZipFile(gtfs_zip_folder)
    df_csv = pd.read_csv(zip_file.open(file_name))
    return df_csv

'''
    Format spatial attributes
'''
# strings to geometry
def format_points(df_points, lon_column, lat_column):
    # Zip the coordinates into a point object and convert to a GeoDataFrame
    geometry = [Point(xy) for xy in zip(df_points[lon_column], df_points[lat_column])]
    gdf_points = gpd.GeoDataFrame(df_points, geometry=geometry)
    del gdf_points[lon_column]
    del gdf_points[lat_column]

    return gdf_points

# group points into linestrings
def format_shape_lines(df_shapes):
    # Zip the coordinates into a point object and convert to a GeoDataFrame
    gdf_points = format_points(df_shapes, 'shape_pt_lon', 'shape_pt_lat')

    # Aggregate these points into a lineString object
    gdf_shapes = gdf_points.groupby(['shape_id'])['geometry'].apply(lambda x: LineString(x.tolist())).reset_index()
    gdf_shapes = gpd.GeoDataFrame(gdf_shapes, geometry='geometry')

    return gdf_shapes

# get line and id from shape_id
def split_shape_id(gdf_shapes, separator):
    s = gdf_shapes['shape_id'].apply(lambda x:x.split(separator))
    gdf_shapes['id'] = s.apply(lambda x: x[-1])
    gdf_shapes['line'] = s.apply(lambda x: x[0])
    del gdf_shapes['shape_id']
    return gdf_shapes

def shapes_to_shapefile(gtfs_zip_folder):
    df_shapes = read_file_in_zip(gtfs_zip_folder, 'shapes.txt')
    gdf_lines = format_shape_lines(df_shapes)
    gdf_lines = split_shape_id(gdf_lines, '.')
    return gdf_lines

def stops_to_shapefile(gtfs_zip_folder):
    df_stops = read_file_in_zip(gtfs_zip_folder, 'stops.txt')
    gdf_stops = format_points(df_stops, 'stop_lon', 'stop_lat')
    return gdf_stops

'''
    Process stop times
'''

def fractionate_trip_id(df_stop_times):
    underline_split = df_stop_times['trip_id'].apply(lambda x:x.split('_'))
    df_stop_times['collect_reference'] = underline_split.apply(lambda x: x[0][0:9])
    df_stop_times['day_type'] = underline_split.apply(lambda x: x[0][9:])
    df_stop_times['trip_id'] = underline_split.apply(lambda x: x[1])
    df_stop_times['trip_id'] = underline_split.apply(lambda x: x[1])
    df_stop_times['line'] = underline_split.apply(lambda x: x[2].split('.')[0])
    df_stop_times['direction'] = underline_split.apply(lambda x: x[2].split('.')[-1][0])
    df_stop_times['vehicle'] = underline_split.apply(lambda x: x[2].split('.')[-1][1:])
    return df_stop_times

def temporal_links_between_stations(df_stop_times):
    link_attributes = []

    previous_stop = df_stop_times.iloc[0]
    for index, current_stop in df_stop_times.loc[1:].iterrows():
        # edges are consecutive stations of each line
        if previous_stop['trip_id'] == current_stop['trip_id']\
         and previous_stop['stop_sequence'] == (current_stop['stop_sequence']-1):
            link_attributes.append({'line': current_stop['line'],\
             'departure_stop': previous_stop['stop_id'], 'departure_time': previous_stop['departure_time'],\
             'arrival_stop': current_stop['stop_id'], 'arrival_time': current_stop['arrival_time'],\
             'direction': current_stop['direction'], 'day_type': current_stop['day_type'],\
             'trip_id': current_stop['trip_id']})
        else:
            print 'link', previous_stop['stop_id'], current_stop['stop_id']
            break
        previous_stop = current_stop
    df_edge_attributes = pd.DataFrame(link_attributes)
    return df_edge_attributes

df_stop_times = read_file_in_zip(gtfs_zip_folder, 'stop_times.txt')
df_stop_times = fractionate_trip_id(df_stop_times)
df_link_attributes = temporal_links_between_stations(df_stop_times)
print df_link_attributes
