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

def group_line_by_trunk(gdf_lines, dict_trunk_names):

    dict_trunk_lines = dict()
    for index, line in gdf_lines.iterrows():
        try:
            trunk_name =  dict_trunk_names[line['shape_id'].split('.')[0]]
        except KeyError:
            trunk_name = 'S'
        finally:
            dict_trunk_lines.setdefault(trunk_name, []).append(line)
            print line['shape_id'], trunk_name

    for trunk, list_lines in dict_trunk_lines.iteritems():
        dict_trunk_lines[trunk] = gpd.GeoDataFrame(list_lines)

    return dict_trunk_lines

def plot_shape_trunk(dict_trunk_lines, line_colors, plot_name):

    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    ax.axis('off')

    for trunk, gdf_lines in dict_trunk_lines.iteritems():
        print trunk, gdf_lines
        try:
            gdf_lines.plot(ax=ax, alpha=0.2, color=line_colors[trunk])
        except KeyError:
            gdf_lines.plot(ax=ax, alpha=0.2, color='#000000')

    fig.savefig(plot_name)

df_shapes = read_file_in_zip(gtfs_zip_folder, 'shapes.txt')
df_stops = read_file_in_zip(gtfs_zip_folder, 'stops.txt')
# print df_shapes
# print df_stops

gdf_lines = format_shape_lines(df_shapes)

nyc_trunk_names = {'1':'1', '2':'1', '3':'1', '4':'4', '5':'4', '6':'4', '7':'7',\
 'A':'A', 'C':'A', 'E':'A', 'B':'B', 'D':'B', 'F':'B', 'M':'B', 'G':'G', 'J':'J',\
 'Z':'J', 'L':'L', 'N':'N','Q':'N','R':'N', 'W':'N', 'S':'S', 'SI':'SI'}

nyc_line_colors = {'1':'#ee352e', '4':'#00933c', '7':'#b933ad', 'A':'#2850ad',\
 'B':'#ff6319', 'G':'#6cbe45', 'J':'#996633', 'L':'#a7a9ac', 'N':'#fccc0a',\
 'S':'#808183'}


# plot_gdf(gdf_lines, result_path + 'shapes.pdf')
dict_trunk_lines = group_line_by_trunk(gdf_lines, nyc_trunk_names)
plot_shape_trunk(dict_trunk_lines, nyc_line_colors, result_path + 'shapes_color.pdf')
