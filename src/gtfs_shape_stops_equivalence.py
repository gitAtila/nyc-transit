'''
    Find the equivalence between shapefile stations and gtfs ones
'''
from sys import argv
import geopandas as gpd
import pandas as pd
import numpy as np
import zipfile

from shapely.geometry import Point

gtfs_zip_folder = argv[1]
shapefile_stops_path = argv[2]
result_path = argv[3]
max_distance = 0.002 #euclidean 

def read_file_in_zip(gtfs_zip_folder, file_name):
    zip_file = zipfile.ZipFile(gtfs_zip_folder)
    df_csv = pd.read_csv(zip_file.open(file_name))
    return df_csv

def format_points(df_points, lon_column, lat_column):
    # Zip the coordinates into a point object and convert to a GeoDataFrame
    geometry = [Point(xy) for xy in zip(df_points[lon_column], df_points[lat_column])]
    gdf_points = gpd.GeoDataFrame(df_points, geometry=geometry)
    del gdf_points[lon_column]
    del gdf_points[lat_column]

    return gdf_points

def nearest_row(point, gdf):
    gdf['distance'] = gdf.apply(lambda row:  point.distance(row.geometry),axis=1)
    geoseries = gdf.iloc[gdf['distance'].argmin()]
    return geoseries

def find_equivalence(gdf_gtfs_stops, gdf_shape_stops):
    list_equivalence = list()
    for index, gtfs_stop in gdf_gtfs_stops.iterrows():
        nearest_shape = nearest_row(gtfs_stop['geometry'], gdf_shape_stops)
        list_equivalence.append((gtfs_stop['stop_id'], nearest_shape['objectid'], nearest_shape['distance']))

    df_equivalence = pd.DataFrame.from_records(list_equivalence, columns=['stop_id', 'objectid', 'distance'])

    return df_equivalence

df_stops = read_file_in_zip(gtfs_zip_folder, 'stops.txt')
gdf_gtfs_stops = format_points(df_stops, 'stop_lon', 'stop_lat')
gdf_gtfs_stops = gdf_gtfs_stops[gdf_gtfs_stops['parent_station'].isnull()]
gdf_gtfs_stops = gdf_gtfs_stops[['stop_id', 'stop_name', 'geometry']]

gdf_shape_stops = gpd.GeoDataFrame.from_file(shapefile_stops_path)

df_equivalence = find_equivalence(gdf_gtfs_stops, gdf_shape_stops)
# It do not consider lage distances
df_equivalence.ix[df_equivalence['distance'] > max_distance, 'objectid'] = None
df_equivalence = df_equivalence.drop(['distance'], axis=1)

df_equivalence.to_csv(result_path+'equivalence_gtfs_shape_stops.csv')
