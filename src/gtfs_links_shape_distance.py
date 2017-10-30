'''
    Get subway links from GTFS and compute distance from Shapefile
'''
from sys import argv
import pandas as pd
import geopandas as gpd
import networkx as nx

import transit_graph as tg
import gtfs_processing as gp

shapefile_stations_path = argv[1]
shapefile_links_path = argv[2]
equivalence_gtfs_shape_stops_path = argv[3]
gtfs_path = argv[4]

results_folder = argv[5]

def links_distance(equivalence_gtfs_shape_stops_path, shapefile_stations_path,\
 shapefile_links_path, gtfs_path):
    list_gtfs_links_distance = []

    gtfs_nyc_subway = gp.TransitFeedProcessing(gtfs_path)
    gdf_subway_stations = gpd.GeoDataFrame.from_file(shapefile_stations_path)
    df_equivalence_gtfs_shape_stops = pd.read_csv(equivalence_gtfs_shape_stops_path)
    del df_equivalence_gtfs_shape_stops['name']

    # geometry links from shape
    nyc_transit_graph = tg.TransitGraph(shapefile_stations_path, shapefile_links_path)

    gdf_shape_links = gpd.GeoDataFrame.from_file(shapefile_links_path)
    df_gtfs_links = gtfs_nyc_subway.distinct_links_between_stations()
    # add gtfs stop_id and line on links
    for index, gtfs_link in df_gtfs_links.iterrows():
    	line = gtfs_link['route_id']
    	gtfs_from_station = gtfs_link['from_parent_station']
    	gtfs_to_station = gtfs_link['to_parent_station']
    	# get shape id
    	shape_from_station = df_equivalence_gtfs_shape_stops[\
    	 df_equivalence_gtfs_shape_stops['stop_id'] == gtfs_from_station]['objectid']
    	shape_to_station = df_equivalence_gtfs_shape_stops[\
    	 df_equivalence_gtfs_shape_stops['stop_id'] == gtfs_to_station]['objectid']

    	if len(shape_from_station) == 1 and len(shape_to_station) == 1:
    		shape_from_station = shape_from_station.iloc[0]
    		shape_to_station = shape_to_station.iloc[0]

    		# get distance from path
    		geometry = gdf_shape_links.query('(@shape_from_station == node_1 and @shape_to_station == node_2)\
    		 or (@shape_from_station == node_2 and @shape_to_station == node_1)')
    		if geometry.empty == False:
    			path_distance = geometry.iloc[0]['shape_len']
    		else:
    			try:
    				path_distance = nyc_transit_graph.shortest_path_length_line(shape_from_station, shape_to_station, line)
    			except:
    				path_distance = nyc_transit_graph.shortest_path_length(shape_from_station, shape_to_station)

    		dict_gtfs_link_distance = gtfs_link.to_dict()
    		dict_gtfs_link_distance['shape_len'] = path_distance
    		list_gtfs_links_distance.append(dict_gtfs_link_distance)
    	else:
    		print 'gtfs_station', gtfs_from_station

    return pd.DataFrame(list_gtfs_links_distance)

df_gtfs_links_distance = links_distance(equivalence_gtfs_shape_stops_path, shapefile_stations_path,\
 shapefile_links_path, gtfs_path)
df_gtfs_links_distance.to_csv(results_folder+'gtfs_links_distance.csv')

print df_gtfs_links_distance
