'''
    Find the equivalence between shapefile stations and gtfs ones
'''
from sys import argv, maxint
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
        list_equivalence.append((gtfs_stop['stop_id'], nearest_shape['objectid'],\
          gtfs_stop['stop_name'], nearest_shape['name'], nearest_shape['distance']))

    df_equivalence = pd.DataFrame.from_records(list_equivalence,\
     columns=['stop_id', 'objectid', 'gtfs_name', 'name', 'distance'])

    return df_equivalence

# read gtfs stops
df_stops = read_file_in_zip(gtfs_zip_folder, 'stops.txt')
gdf_gtfs_stops = format_points(df_stops, 'stop_lon', 'stop_lat')
# get parent stop
gdf_gtfs_stops = gdf_gtfs_stops[gdf_gtfs_stops['parent_station'].isnull()]
gdf_gtfs_stops = gdf_gtfs_stops[['stop_id', 'stop_name', 'geometry']]
print gdf_gtfs_stops[gdf_gtfs_stops['stop_id'] ==  '140']
gdf_gtfs_stops = gdf_gtfs_stops[gdf_gtfs_stops['stop_id'] !=  '140']

# read shapefile stops
gdf_shape_stops = gpd.GeoDataFrame.from_file(shapefile_stops_path)

df_equivalence = find_equivalence(gdf_gtfs_stops, gdf_shape_stops)

# do not consider lage distances
df_equivalence.ix[df_equivalence['distance'] > max_distance, 'objectid'] = -1
df_equivalence = df_equivalence[df_equivalence['objectid'] != -1]
df_equivalence = df_equivalence.drop(['distance'], axis=1)

shape_not_in_equivalence = []
for shape_id in gdf_shape_stops['objectid'].tolist():
    if shape_id not in df_equivalence['objectid'].tolist():
        shape_not_in_equivalence.append(shape_id)

gtfs_not_in_equivalence = []
for gtfs_id in gdf_gtfs_stops['stop_id'].tolist():
    if gtfs_id not in df_equivalence['stop_id'].tolist():
        gtfs_not_in_equivalence.append(gtfs_id)

print 'shape_not_in_equivalence', shape_not_in_equivalence
print ''
print 'gtfs_not_in_equivalence', gtfs_not_in_equivalence

#     stop_id         stop_name                      geometry
# 111     140  South Ferry Loop  POINT (-74.013205 40.701411)
# shape_not_in_equivalence [48.0, 84.0, 124.0, 212.0, 413.0, 422.0, 435.0]
#
# gtfs_not_in_equivalence ['S09', 'S10', 'S11', 'S12', 'S13', 'S14', 'S15', 'S16', 'S17', 'S18', 'S19', 'S20', 'S21', 'S22', 'S23', 'S24', 'S25', 'S26', 'S27', 'S28', 'S29', 'S30', 'S31']


df_equivalence.to_csv(result_path+'equivalence_gtfs_shape_stops.csv')
