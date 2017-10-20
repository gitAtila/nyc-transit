'''
    Read edges and build a graph of the transit system
'''

from sys import argv, maxint
from geopy.distance import vincenty
import pandas as pd
import geopandas as gpd
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

stations_path = argv[1]
links_path = argv[2]
census_tract_path = argv[3]
result_path = argv[4]

__walking_speed = 1.4 # m/s
__subway_speed = 7.59968 # m/s it is 17mph

trunk_colors = {'1':'#ee352e', '4':'#00933c', '7':'#b933ad', 'A':'#2850ad', 'B':'#ff6319',\
 'G':'#6cbe45', 'J':'#996633', 'L':'#a7a9ac', 'N':'#fccc0a', 'T':'#000000'}

'''
    Read stations, subay lines and links between stations
'''

gdf_stations = gpd.GeoDataFrame.from_file(stations_path)
gdf_links = gpd.GeoDataFrame.from_file(links_path)

'''
<<<<<<< HEAD
    Get subway lines and trunks
'''

# get subway trunks
# dict_line_trunk = dict()
# dict_trunk_lines = dict()
# for index, line in gdf_lines.iterrows():
#     dict_line_trunk[line['name']] = line['rt_symbol']
#     dict_trunk_lines.setdefault(line['rt_symbol'],[]).append(line['name'])

'''
    Graph operations
'''

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
    Create subway graph
'''

def create_transit_graph(graph_constructor, gdf_stations, gdf_links):
    g_transit = graph_constructor
    # add stations to subway graph
    for index, station in gdf_stations.iterrows():
        g_transit.add_node(station['objectid'], name=station['name'], line=station['line'],\
         notes=station['notes'], posxy=(station['geometry'].x, station['geometry'].y))

    # add links to subway graph
    for index, link in gdf_links.iterrows():
        if link['node_1'] in g_transit.nodes() and link['node_2'] in g_transit.nodes():
            # compute link distance
            g_transit.add_edge(link['node_1'], link['node_2'], trunk=link['trunk'], distance=link['shape_len'])
        else:
        	print link['node_1'] + 'and' + link['node_2'] + 'are not present in graph'

    return g_transit

'''
    Get the best subway path from a station to a census tract
'''

def stations_near_point_per_trunk(g_transit, gs_point):
    list_trunk_stations = list()
    list_unique_trunks = unique_edge_values(g_transit, 'trunk')
    #print list_unique_trunks
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

def walking_distance_duration(origin, destination):
    distance = vincenty(origin, destination).meters
    duration = distance/__walking_speed
    return {'distance': distance, 'duration': duration}


def station_location_shortest_walk_distance(station_origin, destination_location, g_transit):
    ## get the stations nearby centroid
    dict_trunk_stations_near_destination = stations_near_point_per_trunk(g_transit, destination_location)

    # construct probable trips
    dict_best_trunk_station = best_route_shortest_walk_distance(dict_trunk_stations_near_destination)
    trip_path = nx.dijkstra_path(g_transit, first_subway_boarding, dict_best_trunk_station['station'],\
     weight='distance')

    last_station_location = nx.get_node_attributes(g_transit, 'posxy')[trip_path[-1]]
    destination_location = destination_location.iloc[0]
    destination_location = (destination_location.x, destination_location.y)

    dict_walking_distance_duration = walking_distance_duration(destination_location,\
     last_station_location)

    print dict_walking_distance_duration

    # dict_travel = {'boarding_station': ,'alight_station':, 'transit_distance':, \
    # 'transit_time':, 'walking_distance': , 'walking_time':}

    return trip_path

def location_location_shortest_walk_distance(origin_location, destination_location, g_transit):
    ## get the stations nearby centroid
    dict_trunk_stations_near_origin = stations_near_point_per_trunk(g_transit, origin_location)
    dict_trunk_stations_near_destination = stations_near_point_per_trunk(g_transit, destination_location)

    # construct probable trips
    dict_best_trunk_station_origin = best_route_shortest_walk_distance(dict_trunk_stations_near_origin)
    dict_best_trunk_station_destination = best_route_shortest_walk_distance(dict_trunk_stations_near_destination)

    trip_path = nx.dijkstra_path(g_transit, dict_best_trunk_station_origin['station'],\
     dict_best_trunk_station_destination['station'], weight='distance')

    # dict_travel = {'boarding_station': ,'alight_station':, 'transit_distance':, \
    # 'transit_time':, 'walking_distance': , 'walking_time':}

    return trip_path

'''
=======
>>>>>>> 52b4bb040ac9c640165c481d3369a09f6cc21b6f
    Plot graph
'''

def plot_gdf(gdf, plot_name):
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    ax.axis('off')
    gdf.plot(ax=ax)

    fig.savefig(plot_name)

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

def plot_complete_route(gs_origin, gs_destination, list_stations, transit_graph,\
 trunk_colors, gdf_census_tract, plot_name):
    # plot census tracts of origin and destination

    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    ax.axis('off')
    gs_origin.plot(ax=ax)
    gs_destination.plot(ax=ax)

    # plot stations path
    for station in list_stations:
        posxy = nx.get_node_attributes(transit_graph, 'posxy')[station]
        # print posxy
        # x, y = linestring_s1.xy
        ax.scatter(posxy[0],posxy[1], color='black')

    fig.savefig(plot_name)

'''
    Create subway graph
'''

def create_transit_graph(graph_constructor, gdf_stations, gdf_links):
    g_transit = graph_constructor
    # add stations to subway graph
    for index, station in gdf_stations.iterrows():
        lines = station['line'].split('-')
        g_transit.add_node(station['objectid'], name=station['name'], line=lines,\
         notes=station['notes'], posxy=(station['geometry'].x, station['geometry'].y))

    # add links to subway graph
    for index, link in gdf_links.iterrows():
        if link['node_1'] in g_transit.nodes() and link['node_2'] in g_transit.nodes():
            # compute link distance
            g_transit.add_edge(link['node_1'], link['node_2'], trunk=link['trunk'], distance=link['shape_len'])
        else:
        	print link['node_1'] + 'and' + link['node_2'] + 'are not present in graph'

    return g_transit

'''
    Graph operations
'''

def get_subgraph_node(graph, node_key, node_value):
    list_node = []
    for key, dict_attribute in graph.nodes_iter(data=True):
        if type(dict_attribute[node_key]) == list:
            if node_value in dict_attribute[node_key]:
                list_node.append(key)
        elif dict_attribute[node_key] == node_value:
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
    list_values = []
    for index in graph:
        value = graph.node[index][node_key]
        if type(value) != list:
            list_values.append(value)
        else:
            for item in value:
                list_values.append(item)

    return set(list_values)

def unique_edge_values(graph, edge_key):
    list_attribute = []
    for u, v, dict_attribute in graph.edges_iter(data=True):
        list_attribute.append(dict_attribute[edge_key])
    return list(set(list_attribute))

def distance_points(point_lon_lat_A, point_lon_lat_B):
    return vincenty((point_lon_lat_A[1], point_lon_lat_A[0]),\
     (point_lon_lat_B[1], point_lon_lat_B[0])).meters

'''
    Get the best subway path from a station to a census tract
'''

def stations_near_point_per_trunk(g_transit, gs_point):
    list_trunk_stations = list()
    list_unique_trunks = unique_edge_values(g_transit, 'trunk')
    #print list_unique_trunks
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

def stations_near_point_per_line(g_transit, gs_point):
    list_trunk_stations = list()
    list_unique_lines = unique_node_values(g_transit, 'line')
    print list_unique_lines

    # Find the nearest station from point for each line
    dict_stations_line = dict()
    for line in list_unique_lines:
        g_line = get_subgraph_node(g_transit, 'line', line)

        # get the nearest station
        shortest_distance = maxint
        best_station = -1
        for node_key, dict_attribute in g_line.nodes_iter(data=True):
            distance =  distance_points(dict_attribute['posxy'], (gs_point.iloc[0].x, gs_point.iloc[0].y))
            if distance < shortest_distance:
                shortest_distance = distance
                best_station = node_key
        dict_stations_line[line] = {'station':best_station ,'distance': shortest_distance}

    return dict_stations_line

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

def station_location_shortest_walk_distance(g_transit, origin_station, destination_location):
    ## get the stations nearby destination point
    dict_trunk_stations_near_destination = stations_near_point_per_trunk(g_transit, destination_location)

    # construct probable trips
    dict_best_trunk_station = best_route_shortest_walk_distance(dict_trunk_stations_near_destination)
    path_stations = nx.shortest_path(g_transit, origin_station, dict_best_trunk_station['station'],\
     weight='distance')

    path_length = nx.shortest_path_length(g_transit, origin_station, dict_best_trunk_station['station'],\
     weight='distance')

    print path_stations
    print dict_best_trunk_station
    print path_length

    return path_stations

def station_location_all_lines(g_transit, origin_station, destination_location):
    list_routes = []
    ## get the stations nearby destination point
    dict_line_stations_near_destination = stations_near_point_per_line(g_transit, destination_location)

    # construct probable trips
    for line, dict_station in dict_line_stations_near_destination.iteritems():
        path_stations = nx.shortest_path(g_transit, origin_station, dict_station['station'],\
         weight='distance')
        path_length = nx.shortest_path_length(g_transit, origin_station, dict_station['station'],\
         weight='distance')

        # stations of integration
        list_distinct_lines = []
        previous_lines = sorted(g_transit.node[origin_station]['line'])
        list_distinct_lines.append({'station': origin_station, 'lines': previous_lines})

        for index in range(1, len(path_stations)):
            station = path_stations[index]
            previous_lines = list_distinct_lines[-1]['lines']
            current_lines = sorted(g_transit.node[station]['line'])
            intersection_lines = sorted(list(set(previous_lines) & set(current_lines)))

            # there is an itegration
            if len(intersection_lines) == 0:
                list_distinct_lines.append({'station': station, 'lines': current_lines})

            # remove from the previous lines the ones that is not in the current lines
            elif current_lines != previous_lines and previous_lines != intersection_lines:
                previous_lines = intersection_lines
                previous_station = list_distinct_lines[-1]['station']
                del list_distinct_lines[-1]
                list_distinct_lines.append({'station': previous_station, 'lines': previous_lines})

        #print path_stations
        print 'last_line', line
        print 'subway_distance', path_length
        print 'walking_distance', dict_station['distance']
        print 'last_station', dict_station['station']
        print 'boardings', list_distinct_lines
        print ''

        list_routes.append({'last_line': line,'subway_distance': path_length,\
         'walking_distance': dict_station['distance'], 'last_station': dict_station['station'],\
         'boardings': list_distinct_lines})

    return list_routes

def location_location_all_lines(g_transit, origin_location, destination_location):
    list_routes = []
    ## get the stations nearby destination point
    dict_line_stations_near_origin = stations_near_point_per_line(g_transit, origin_location)
    dict_line_stations_near_destination = stations_near_point_per_line(g_transit, destination_location)

    # construct probable trips
    for line_origin, dict_station_origin in dict_line_stations_near_origin.iteritems():
        for line_destination, dict_station_destination in dict_line_stations_near_destination.iteritems():
            origin_station = dict_station_origin['station']
            destination_station = dict_station_destination['station']

            # get path and distance between first boaring and last alight
            path_stations = nx.shortest_path(g_transit, origin_station,\
             dict_station_destination['station'], weight='distance')
            path_length = nx.shortest_path_length(g_transit, destination_station,\
             dict_station_destination['station'], weight='distance')

            # stations of integration
            list_distinct_lines = []
            previous_lines = sorted(g_transit.node[origin_station]['line'])
            list_distinct_lines.append({'station': origin_station, 'lines': previous_lines})

            for index in range(1, len(path_stations)):
                station = path_stations[index]
                previous_lines = list_distinct_lines[-1]['lines']
                current_lines = sorted(g_transit.node[station]['line'])
                intersection_lines = sorted(list(set(previous_lines) & set(current_lines)))

                # there is an itegration
                if len(intersection_lines) == 0:
                    list_distinct_lines.append({'station': station, 'lines': current_lines})

                # remove from the previous lines the ones that is not in the current lines
                elif current_lines != previous_lines and previous_lines != intersection_lines:
                    previous_lines = intersection_lines
                    previous_station = list_distinct_lines[-1]['station']
                    del list_distinct_lines[-1]
                    list_distinct_lines.append({'station': previous_station, 'lines': previous_lines})

            #print path_stations
            print 'walking_distance_origin', dict_station_origin['distance']
            print 'first_station', dict_station_origin['station']
            print 'first_line', line_origin
            print 'boardings', list_distinct_lines
            print 'subway_distance', path_length
            print 'walking_distance_destination', dict_station_destination['distance']
            print 'last_station', dict_station_destination['station']
            print 'last line', line_destination

            print ''

            list_routes.append({'walking_distance_origin': dict_station_origin['distance'],\
             'first_station': dict_station_origin['station'],\
             'first_line': line_origin, 'boardings': list_distinct_lines,\
             'subway_distance': path_length,\
             'walking_distance_destination': dict_station_destination['distance'],\
             'last_station': dict_station_destination['station'],\
             'last line': line_destination})

    return list_routes

'''
    Test area
'''
g_transit = create_transit_graph(nx.Graph(), gdf_stations, gdf_links)
#g_transit = create_transit_graph(nx.MultiGraph(), gdf_stations, df_links)
#split_line_route(gdf_stations, gdf_lines, df_links)

gdf_census_tract = gpd.GeoDataFrame.from_file(census_tract_path)
first_subway_boarding = 49
ct_origin = '012600'
boro_origin = '1'
ct_destination = '024100'
boro_destination = '2'

gs_origin = gdf_census_tract[gdf_census_tract['ct2010'] == ct_origin]
gs_origin = gs_origin[gs_origin['boro_code'] == boro_origin]
origin_centroid = gs_origin.centroid

# discover which was the alight station
## get the centroid of the census tract
gs_destination = gdf_census_tract[gdf_census_tract['ct2010'] == ct_destination]
gs_destination = gs_destination[gs_destination['boro_code'] == boro_destination]
destination_centroid = gs_destination.centroid

<<<<<<< HEAD
trip_station_location = station_location_shortest_walk_distance(first_subway_boarding,\
 destination_centroid, g_transit)
print trip_station_location
for station in trip_station_location:
    print station, '\t' + gdf_stations[gdf_stations['objectid'] == station]['line'].iloc[0]

trip_location_location = location_location_shortest_walk_distance(origin_centroid,\
 destination_centroid, g_transit)
print trip_location_location

for station in trip_location_location:
    print station, '\t' + gdf_stations[gdf_stations['objectid'] == station]['line'].iloc[0]
    #print station
#plot_path(g_transit, trip_path, result_path+'passenger_path.pdf')
# plot_complete_route(gs_origin, gs_destination, trip_path, g_transit,\
#  trunk_colors, gdf_census_tract, result_path+'ct_od.png')
=======
#station_location_shortest_walk_distance(g_transit, first_subway_boarding, destination_centroid)
#station_location_all_lines(g_transit, first_subway_boarding, destination_centroid)
location_location_all_lines(g_transit, origin_centroid, destination_centroid)

#plot_path(g_transit, trip_path, result_path+'passenger_path.pdf')
# plot_complete_route(gs_origin, gs_destination, trip_path, g_transit,\
#  trunk_colors, gdf_census_tract, result_path+'ct_od.png')

# dict_trip_trunks = dict()
# for trunk, destination_station in trunk_stations.iteritems():
#     print trunk, destination_station
#     trip_path = nx.dijkstra_path(g_transit, first_subway_boarding, destination_station['station'],\
#      weight='distance')
#     dict_trip_trunks[trunk] = trip_path
#     print trip_path
#     print ''
>>>>>>> 52b4bb040ac9c640165c481d3369a09f6cc21b6f
