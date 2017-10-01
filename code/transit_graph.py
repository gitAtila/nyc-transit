#read edges and build a graph of the transit system
from sys import argv, maxint
from geopy.distance import vincenty
import pandas as pd
import geopandas as gpd
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

from shapely.geometry import Point

stations_path = argv[1]
lines_path = argv[2]
links_path = argv[3]
census_tract_path = argv[4]
result_folder = argv[5]

def get_subgraph_node(graph, node_key, node_value):
    list_node = []
    for key, dict_attribute in graph.nodes_iter(data=True):
        if dict_attribute[node_key] == node_value:
            list_node.append(key)
    subgraph = graph.subgraph(list_node)
    return subgraph

def get_subgraph_edge(graph, edge_key, edge_value):
    list_node = []
    for u, v, dict_attribute in graph.edges_iter(data=True):
        if dict_attribute[edge_key] == edge_value:
            if u not in list_node:
                list_node.append(u)
            if v not in list_node:
                list_node.append(v)
    return graph.subgraph(list_node)

def unique_node_values(graph, node_key):
    return list(set([graph.node[index][node_key] for index in graph]))

def unique_edge_values(graph, edge_key):
    list_attribute = []
    for u, v, dict_attribute in graph.edges_iter(data=True):
        list_attribute.append(dict_attribute[edge_key])
    return list(set(list_attribute))

def distance_points(point_lon_lat_A, point_lon_lat_B):
    return vincenty((point_lon_lat_A[1], point_lon_lat_A[0]),\
     (point_lon_lat_B[1], point_lon_lat_B[0])).meters

'''
    Read stations, subay lines and links between stations
'''

gdf_stations = gpd.GeoDataFrame.from_file(stations_path)
gdf_lines = gpd.GeoDataFrame.from_file(lines_path)
df_links = pd.read_csv(links_path)

'''
    Get subway lines and trunks
'''

# get subway trunks
dict_line_trunk = dict()
dict_trunk_lines = dict()
for index, line in gdf_lines.iterrows():
    dict_line_trunk[line['name']] = line['rt_symbol']
    dict_trunk_lines.setdefault(line['rt_symbol'],[]).append(line['name'])

'''
    Create subway graph
'''

def create_transit_graph(graph_constructor, gdf_stations, df_links):
    g_transit = graph_constructor
    # add stations to subway graph
    for index, station in gdf_stations.iterrows():
        g_transit.add_node(station['objectid'], name=station['name'], line=station['line'],\
         notes=station['notes'], posxy=(station['geometry'].x, station['geometry'].y))

    # add links to subway graph
    for index, link in df_links.iterrows():
        if link['node_1'] in g_transit.nodes() and link['node_2'] in g_transit.nodes():
            # compute link distance
            distance = distance_points(g_transit.node[link['node_1']]['posxy'], g_transit.node[link['node_2']]['posxy'])
            g_transit.add_edge(link['node_1'], link['node_2'], trunk=link['trunk'], distance=distance)
        else:
        	print link['node_1'] + 'and' + link['node_2'] + 'are not present in graph'

    return g_transit

def path_between_stops(stop_1, stop_2, trunk_line):
    print stop_1
    print stop_2
    print trunk_line


g_transit = create_transit_graph(nx.Graph(), gdf_stations, df_links)
#g_transit = create_transit_graph(nx.MultiGraph(), gdf_stations, df_links)
#split_line_route(gdf_stations, gdf_lines, df_links)
for index, link in df_links.iterrows():

    stop_1 = gdf_stations[gdf_stations['objectid'] == link['node_1']]
    stop_2 = gdf_stations[gdf_stations['objectid'] == link['node_2']]

    gdf_trunk_line = gdf_lines[gdf_lines['rt_symbol'] == link['trunk']]

    # find the nearest linestrings
    min_distance_s1 = maxint
    min_distance_s2 = maxint
    closest_linestring_s1 = -1
    closest_linestring_s2 = -1
    for index, linestring in gdf_trunk_line.iterrows():
        distance_s1 = float(stop_1.distance(linestring['geometry']))
        distance_s2 = float(stop_2.distance(linestring['geometry']))
        #print index, float(distance_s1), float(distance_s2)
        if distance_s1 < min_distance_s1:
            min_distance_s1 = distance_s1
            closest_linestring_s1 = linestring['id']

        if distance_s2 < min_distance_s2:
            min_distance_s2 = distance_s2
            closest_linestring_s2 = linestring['id']

    print min_distance_s1, closest_linestring_s1
    print min_distance_s2, closest_linestring_s2

    gdf_trunk_line_s1 = gdf_trunk_line[gdf_trunk_line['id'] == closest_linestring_s1]
    gdf_trunk_line_s2 = gdf_trunk_line[gdf_trunk_line['id'] == closest_linestring_s2]

    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    ax.axis('off')
    gdf_trunk_line_s1.plot(ax=ax, alpha=0.2, color='blue')
    if closest_linestring_s1 != closest_linestring_s2:
        gdf_trunk_line_s2.plot(ax=ax, alpha=0.2, color='blue')
    stop_1.plot(ax=ax, marker='*', color='black', markersize=2)
    stop_2.plot(ax=ax, marker='*', color='black', markersize=2)
    fig.savefig(result_folder + 'path_between_stops.pdf')

    break

'''
    Get the best subway path from one station to a census tract
'''

def stations_near_point_per_trunk(g_transit, gs_point):
    list_trunk_stations = list()
    list_unique_trunks = unique_edge_values(g_transit, 'trunk')
    print list_unique_trunks
    # Find out the nearest station from point for each line trunk
    dict_stations_trunk = dict()
    for trunk in list_unique_trunks:
        g_trunk = get_subgraph_edge(g_transit, 'trunk', trunk)
        # get the nearest station
        shortest_distance = maxint
        best_station = -1
        for node_key, dict_attribute in g_trunk.nodes_iter(data=True):
            distance =  distance_points(dict_attribute['posxy'], (gs_point.iloc[0].x, gs_point.iloc[0].y))
            if distance < shortest_distance:
                shortest_distance = distance
                best_station = node_key
        dict_stations_trunk[trunk] = {'station':best_station ,'distance': shortest_distance}

    # stations of transference were already inserted
    del dict_stations_trunk['T']

    return dict_stations_trunk

def best_route_shortest_walk_distance(dict_trip_trunks):
    shortest_distance = maxint
    nearest_trunk = -1
    for trunk, destination_station in dict_trip_trunks.iteritems():
        if destination_station['distance'] < shortest_distance:
            shortest_distance = destination_station['distance']
            nearest_trunk = trunk

    best_destination = dict_trip_trunks[nearest_trunk]
    best_destination['trunk'] = nearest_trunk

    return best_destination

gdf_census_tract = gpd.GeoDataFrame.from_file(census_tract_path)
first_subway_boarding = 49
ct_origin = '012600'
ct_destination = '024100'
boro_destination = '2'

# discover which was the alight station
## get the centroid of the census tract
gs_destination = gdf_census_tract[gdf_census_tract['ct2010'] == ct_destination]
gs_destination = gs_destination[gs_destination['boro_code'] == boro_destination]
destination_centroid = gs_destination.centroid

## get the stations nearby centroid
dict_trunk_stations_near_destination = stations_near_point_per_trunk(g_transit, destination_centroid)

# construct probable trips
dict_best_trunk_station = best_route_shortest_walk_distance(dict_trunk_stations_near_destination)
trip_path = nx.dijkstra_path(g_transit, first_subway_boarding, dict_best_trunk_station['station'],\
 weight='distance')

# dict_trip_trunks = dict()
# for trunk, destination_station in trunk_stations.iteritems():
#     print trunk, destination_station
#     trip_path = nx.dijkstra_path(g_transit, first_subway_boarding, destination_station['station'],\
#      weight='distance')
#     dict_trip_trunks[trunk] = trip_path
#     print trip_path
#     print ''

'''
    Plot graph
'''

def plot_graph(graph, unique_keys, color_field,  file_name):
    print unique_keys
    # set colors to stations acording with its line
    color_map = dict()
    cmap = plt.get_cmap('prism')
    colors = cmap(np.linspace(0,1,len(unique_keys)))
    for key in range(len(unique_keys)):
        color_map[unique_keys[key]] = colors[key]
    #plot color
    positions = nx.get_node_attributes(graph, 'posxy')
    node_color=[color_map[graph.node[node][color_field]] for node in graph]
    nx.draw(graph, positions, node_color=node_color, cmap=plt.get_cmap('jet'), node_size=5,\
     font_size=5, with_labels=False)
    plt.savefig(file_name, dpi=1000)

def plot_transit_graph(transit_graph, result_file_name):
    # # set nodes color according to lines
    # ## get unique lines
    # unique_lines = list(gdf_stations['line'].unique())
    # ## define color range
    # cmap = plt.get_cmap('prism')
    # ## set color to nodes
    # colors = cmap(np.linspace(0,1,len(unique_lines)))
    # color_map = dict()
    # for line in range(len(unique_lines)):
    #     color_map[unique_lines[line]] = colors[line]
    # node_color = [color_map[transit_graph.node[node]['line']] for node in transit_graph]
    node_color = '#000000'

    # set edges color according to trunks
    ## get official colors
    trunk_colors = {'1':'#ee352e', '4':'#00933c', '7':'#b933ad', 'A':'#2850ad', 'B':'#ff6319',\
     'G':'#6cbe45', 'J':'#996633', 'L':'#a7a9ac', 'N':'#fccc0a', 'T':'#000000'}
    ## set colors to edges
    edge_color = [trunk_colors[transit_graph[u][v]['trunk']] for u,v in transit_graph.edges()]
    #edge_color = '#ff6319'

    # set node positions according to geographical positions of stations
    node_position = nx.get_node_attributes(transit_graph, 'posxy')

    # plot and save graph
    nx.draw(transit_graph, node_position, node_color=node_color, edge_color=edge_color,\
     node_size=1, alpha=0.5, linewidths=0.5 , with_labels=False)
    plt.savefig(result_file_name, dpi=1000)

def plot_path(transit_graph, list_stations, result_file_name):
    # plot complete transit graph
    node_position = nx.get_node_attributes(transit_graph, 'posxy')
    node_color = '#000000'
    edge_color = '#a7a9ac'
    nx.draw(transit_graph, node_position, node_color=node_color, edge_color=edge_color,\
     node_size=1, alpha=0.2, linewidths=0.5 , with_labels=False)

    # plot trip path
    trip_path = transit_graph.subgraph(list_stations)
    node_position = nx.get_node_attributes(trip_path, 'posxy')
    node_color = '#a7a9ac'
    edge_color = '#000000'
    nx.draw(trip_path, node_position, node_color=node_color, edge_color=edge_color,\
     node_size=1, alpha=1, linewidths=0.5 , with_labels=False)

    plt.savefig(result_file_name, dpi=1000)

#plot_transit_graph(g_transit, result_folder + 'transit_graph_overlapped.png')
plot_path(g_transit, trip_path, result_folder + 'transit_graph_path.png')

#graph_trunk_1 = nx.Graph((u,v,attribute) for u, v, attribute in g_transit.edges_iter(data=True) if attribute['trunk']=='1')
# graph_trunk_1 = get_subgraph_node(g_transit, )
# for node in graph_trunk_1.nodes():
#     print graph_trunk_1[node]
# plot_transit_graph(graph_trunk_1, result_folder + 'transit_graph_1.png')
'''
unique_line_trunks = list(set([g_transit.node[index]['trunk'] for index in g_transit]))
unique_lines = list(gdf_stations['line'].unique())

#sg_transit = sorted(nx.connected_component_subgraphs(g_transit), key = len, reverse=True)[0]
plot_graph(g_transit, unique_lines, 'line', 'subway_trunk_all.png')
#plot_graph(g_transit, unique_line_trunks, 'trunk', 'subway_trunk_all.pdf')
'''
