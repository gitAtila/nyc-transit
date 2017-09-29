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

def format_shape_lines(df_shapes):
    # Zip the coordinates into a point object and convert to a GeoDataFrame
    geometry = [Point(xy) for xy in zip(df_shapes['shape_pt_lon'], df_shapes['shape_pt_lat'])]
    gdf_shapes = gpd.GeoDataFrame(df_shapes, geometry=geometry)

    # Aggregate these points into a lineString object
    gdf_shapes = gdf_shapes.groupby(['shape_id'])['geometry'].apply(lambda x: LineString(x.tolist())).reset_index()
    gdf_shapes = gpd.GeoDataFrame(gdf_shapes, geometry='geometry')

    return gdf_shapes

def plot_gdf(gdf, plot_name):
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    gdf.plot(ax=ax)

    fig.savefig(plot_name)

df_shapes = read_file_in_zip(gtfs_zip_folder, 'shapes.txt')
df_stops = read_file_in_zip(gtfs_zip_folder, 'stops.txt')
# print df_shapes
# print df_stops

gdf_lines = format_shape_lines(df_shapes)
print gdf_lines
plot_gdf(gdf_lines, result_path + 'shapes.pdf')
