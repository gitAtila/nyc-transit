'''
    Read GTFS file and plot stops and connections
'''

from sys import argv
import os
import zipfile

import pandas as pd

import geopandas as gpd
from geopy.distance import vincenty
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
    #gdf_lines = split_shape_id(gdf_lines, '.')
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

# from:https://stackoverflow.com/questions/34754777/shapely-split-linestrings-at-intersections-with-other-linestrings
def cut_line_at_points(line, points):
    # First coords of line
    coords = list(line.coords)

    # Keep list coords where to cut (cuts = 1)
    cuts = [0] * len(coords)
    cuts[0] = 1
    cuts[-1] = 1

    # Add the coords from the points
    coords += [list(p.coords)[0] for p in points]
    cuts += [1] * len(points)

    # Calculate the distance along the line for each point
    dists = [line.project(Point(p)) for p in coords]

    # sort the coords/cuts based on the distances
    coords = [p for (d, p) in sorted(zip(dists, coords))]
    cuts = [p for (d, p) in sorted(zip(dists, cuts))]

    # generate the Lines
    lines = []
    for i in range(len(coords)-1):
        if cuts[i] == 1:
            # find next element in cuts == 1 starting from index i + 1
            j = cuts.index(1, i + 1)
            lines.append(LineString(coords[i:j+1]))

    return lines

def distance_linestring(linestring):
    total_distance = 0
    previous_position = linestring.coords[0]
    for index in range(1, len(linestring.coords)):
        current_position = linestring.coords[index]
        total_distance += vincenty(previous_position, current_position).meters
        previous_position = current_position
    return total_distance

def links_between_stations(gtfs_zip_folder):
    df_stop_times = read_file_in_zip(gtfs_zip_folder, 'stop_times.txt')
    df_trips = read_file_in_zip(gtfs_zip_folder, 'trips.txt')

    gdf_stops = stops_to_shapefile(gtfs_zip_folder)
    gdf_shapes = shapes_to_shapefile(gtfs_zip_folder)
    link_attributes = []

    previous_stop = df_stop_times.iloc[0]
    for index, current_stop in df_stop_times.loc[1:].iterrows():
        # edges are consecutive stations of each line
        if previous_stop['trip_id'] == current_stop['trip_id']\
         and previous_stop['stop_sequence'] == (current_stop['stop_sequence']-1):

            from_stop_id = previous_stop['stop_id']
            to_stop_id = current_stop['stop_id']
            trip_id = current_stop['trip_id']

            # get positions of stops
            from_stop = gdf_stops[gdf_stops['stop_id'] == from_stop_id]
            to_stop = gdf_stops[gdf_stops['stop_id'] == to_stop_id]

            # get linestring of line
            s_trip = df_trips[df_trips['trip_id'] == trip_id]
            s_line = gdf_shapes[gdf_shapes['shape_id'] == s_trip['shape_id'].iloc[0]]

            # cut linestring by stations
            link_linestring = cut_line_at_points(s_line['geometry'].iloc[0], [from_stop['geometry'].iloc[0],\
             to_stop['geometry'].iloc[0]])[1]

            link_distance = distance_linestring(link_linestring)

            link_attributes.append({'route_id': s_trip['route_id'].iloc[0], 'trip_id': trip_id,\
             'from_stop_id': from_stop_id, 'departure_time': previous_stop['departure_time'],\
             'to_stop_id': to_stop_id, 'arrival_time': current_stop['arrival_time'],\
             'trip_headsign': s_trip['trip_headsign'].iloc[0], 'shape_dist_traveled': link_distance})

        else:
            print 'link', previous_stop['stop_id'], current_stop['stop_id']
            break
        previous_stop = current_stop
    df_edge_attributes = pd.DataFrame(link_attributes)
    return df_edge_attributes

df_temporal_links = temporal_links_between_stations(gtfs_zip_folder)
print df_temporal_links
