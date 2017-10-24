'''
    Read edges and build a transit_graph of the transit system
'''

from sys import argv, maxint
from geopy.distance import vincenty
import pandas as pd
import geopandas as gpd
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

# stations_path = argv[1]
# links_path = argv[2]
# census_tract_path = argv[3]
# result_path = argv[4]

# __walking_speed = 1.4 # m/s
# __subway_speed = 7.59968 # m/s it is 17mph

# trunk_colors = {'1':'#ee352e', '4':'#00933c', '7':'#b933ad', 'A':'#2850ad', 'B':'#ff6319',\
#  'G':'#6cbe45', 'J':'#996633', 'L':'#a7a9ac', 'N':'#fccc0a', 'T':'#000000'}

class TransitGraph:

    '''
        Read stations, subay lines and links between stations
    '''
    def __init__(self, stations_path, geolinks_path, census_tract_path):
        self.gdf_stations = gpd.GeoDataFrame.from_file(stations_path)
        self.gdf_links = gpd.GeoDataFrame.from_file(links_path)
        self.gdf_census_tract = gpd.GeoDataFrame.from_file(census_tract_path)
        self.transit_graph = self.create_transit_graph()

    '''
        Plot transit_graph
    '''

    def plot_gdf(gdf, plot_name):
        fig, ax = plt.subplots()
        ax.set_aspect('equal')
        ax.axis('off')
        gdf.plot(ax=ax)

        fig.savefig(plot_name)

    def plot_graph(self, color_field,  file_name):
        unique_keys = list(self.gdf_stations['trunk'].unique())
        # set colors to stations acording with its line
        color_map = dict()
        cmap = plt.get_cmap('prism')
        colors = cmap(np.linspace(0,1,len(unique_keys)))
        for key in range(len(unique_keys)):
            color_map[unique_keys[key]] = colors[key]
        #plot color
        positions = nx.get_node_attributes(self.transit_graph, 'posxy')
        node_color=[color_map[self.transit_graph.node[node][color_field]] for node in self.transit_graph]
        nx.draw(self.transit_graph, positions, node_color=node_color, cmap=plt.get_cmap('jet'), node_size=5,\
         font_size=5, with_labels=False)
        plt.savefig(file_name, dpi=1000)

    def plot_transit_graph(self, result_file_name):
        # # set nodes color according to lines
        # ## get unique lines
        # unique_lines = list(self.gdf_stations['line'].unique())
        # ## define color range
        # cmap = plt.get_cmap('prism')
        # ## set color to nodes
        # colors = cmap(np.linspace(0,1,len(unique_lines)))
        # color_map = dict()
        # for line in range(len(unique_lines)):
        #     color_map[unique_lines[line]] = colors[line]
        # node_color = [color_map[self.transit_graph.node[node]['line']] for node in self.transit_graph]
        node_color = '#000000'

        # set edges color according to trunks
        ## get official colors
        trunk_colors = {'1':'#ee352e', '4':'#00933c', '7':'#b933ad', 'A':'#2850ad', 'B':'#ff6319',\
         'G':'#6cbe45', 'J':'#996633', 'L':'#a7a9ac', 'N':'#fccc0a', 'T':'#000000'}
        ## set colors to edges
        edge_color = [trunk_colors[self.transit_graph[u][v]['trunk']] for u,v in self.transit_graph.edges()]
        #edge_color = '#ff6319'

        # set node positions according to geographical positions of stations
        node_position = nx.get_node_attributes(self.transit_graph, 'posxy')

        # plot and save self.transit_graph
        nx.draw(self.transit_graph, node_position, node_color=node_color, edge_color=edge_color,\
         node_size=1, alpha=0.5, linewidths=0.5 , with_labels=False)
        plt.savefig(result_file_name, dpi=1000)

    def plot_path(self, list_stations, result_file_name):
        # plot complete transit self.transit_graph
        node_position = nx.get_node_attributes(self.transit_graph, 'posxy')
        node_color = '#000000'
        edge_color = '#a7a9ac'
        nx.draw(self.transit_graph, node_position, node_color=node_color, edge_color=edge_color,\
         node_size=1, alpha=0.2, linewidths=0.5 , with_labels=False)

        # plot trip path
        trip_path = self.transit_graph.subgraph(list_stations)
        node_position = nx.get_node_attributes(trip_path, 'posxy')
        node_color = '#a7a9ac'
        edge_color = '#000000'
        nx.draw(trip_path, node_position, node_color=node_color, edge_color=edge_color,\
         node_size=1, alpha=1, linewidths=0.5 , with_labels=False)

        plt.savefig(result_file_name, dpi=1000)

    def plot_complete_route(self, gs_origin, gs_destination, list_stations, \
     trunk_colors, plot_name):
        # plot census tracts of origin and destination

        fig, ax = plt.subplots()
        ax.set_aspect('equal')
        ax.axis('off')
        gs_origin.plot(ax=ax)
        gs_destination.plot(ax=ax)

        # plot stations path
        for station in list_stations:
            posxy = nx.get_node_attributes(self.transit_graph, 'posxy')[station]
            # print posxy
            # x, y = linestring_s1.xy
            ax.scatter(posxy[0],posxy[1], color='black')

        fig.savefig(plot_name)

    '''
        Create subway transit_graph
    '''

    def create_transit_graph(self):
        transit_graph = nx.Graph()
        # add stations to subway transit_graph
        for index, station in self.gdf_stations.iterrows():
            lines = station['line'].split('-')
            transit_graph.add_node(station['objectid'], name=station['name'], line=lines,\
             notes=station['notes'], posxy=(station['geometry'].x, station['geometry'].y))

        # add links to subway transit_graph
        for index, link in self.gdf_links.iterrows():
            if link['node_1'] in transit_graph.nodes() and link['node_2'] in transit_graph.nodes():
                # compute link distance
                transit_graph.add_edge(link['node_1'], link['node_2'], trunk=link['trunk'], distance=link['shape_len'])
            else:
            	print link['node_1'] + 'and' + link['node_2'] + 'are not present in transit_graph'

        return transit_graph

    '''
        Graph operations
    '''

    def get_subgraph_node(self, node_key, node_value):
        list_node = []
        for key, dict_attribute in self.transit_graph.nodes_iter(data=True):
            if type(dict_attribute[node_key]) == list:
                if node_value in dict_attribute[node_key]:
                    list_node.append(key)
            elif dict_attribute[node_key] == node_value:
                list_node.append(key)
        subgraph = self.transit_graph.subgraph(list_node)
        return subgraph

    def get_subgraph_edge(self, edge_key, edge_value):
        list_node = []
        for u, v, dict_attribute in self.transit_graph.edges_iter(data=True):
            if dict_attribute[edge_key] == edge_value:
                if u not in list_node:
                    list_node.append(u)
                if v not in list_node:
                    list_node.append(v)
        return self.transit_graph.subgraph(list_node)

    def unique_node_values(self, node_key):
        list_values = []
        for index in self.transit_graph:
            value = self.transit_graph.node[index][node_key]
            if type(value) != list:
                list_values.append(value)
            else:
                for item in value:
                    list_values.append(item)

        return set(list_values)

    def unique_edge_values(self, edge_key):
        list_attribute = []
        for u, v, dict_attribute in self.transit_graph.edges_iter(data=True):
            list_attribute.append(dict_attribute[edge_key])
        return list(set(list_attribute))

    def distance_points(self, point_lon_lat_A, point_lon_lat_B):
        return vincenty((point_lon_lat_A[1], point_lon_lat_A[0]),\
         (point_lon_lat_B[1], point_lon_lat_B[0])).meters

    '''
        Get the best subway path from a station to a census tract
    '''

    def stations_near_point_per_trunk(self, gs_point):
        list_trunk_stations = list()
        list_unique_trunks = unique_edge_values(self.transit_graph, 'trunk')
        #print list_unique_trunks
        # Find out the nearest station from point for each line trunk
        dict_stations_trunk = dict()
        for trunk in list_unique_trunks:
            g_trunk = get_subgraph_edge(self.transit_graph, 'trunk', trunk)
            # get the nearest station
            shortest_distance = maxint
            best_station = -1
            for node_key, dict_attribute in g_trunk.nodes_iter(data=True):
                distance =  self.distance_points(dict_attribute['posxy'], (gs_point.iloc[0].x, gs_point.iloc[0].y))
                if distance < shortest_distance:
                    shortest_distance = distance
                    best_station = node_key
            dict_stations_trunk[trunk] = {'station':best_station ,'distance': shortest_distance}

        # stations of transference were already inserted
        del dict_stations_trunk['T']

        return dict_stations_trunk

    def stations_near_point_per_line(self, gs_point):
        list_trunk_stations = list()
        list_unique_lines = self.unique_node_values('line')
        #print list_unique_lines

        # Find the nearest station from point for each line
        dict_stations_line = dict()
        for line in list_unique_lines:
            g_line = self.get_subgraph_node('line', line)

            # get the nearest station
            shortest_distance = maxint
            best_station = -1
            for node_key, dict_attribute in g_line.nodes_iter(data=True):
                distance =  self.distance_points(dict_attribute['posxy'], (gs_point.iloc[0].x, gs_point.iloc[0].y))
                if distance < shortest_distance:
                    shortest_distance = distance
                    best_station = node_key
            dict_stations_line[line] = {'station':best_station ,'distance': shortest_distance}

        return dict_stations_line

    def best_route_shortest_walk_distance(self, dict_trip, key_name):
        shortest_distance = maxint
        nearest_key = -1
        for key_value, destination_station in dict_trip.iteritems():
            if destination_station['distance'] < shortest_distance:
                shortest_distance = destination_station['distance']
                nearest_key = key_value

        best_destination = dict_trip[nearest_key]
        best_destination[key_name] = nearest_key

        return best_destination

    def station_location_shortest_walk_distance(self, origin_station, destination_location):
        ## get the stations nearby destination point
        dict_line_stations_near_destination = self.stations_near_point_per_line(destination_location)

        # construct probable trips
        #print dict_line_stations_near_destination
        dict_last_station = self.best_route_shortest_walk_distance(dict_line_stations_near_destination, 'line')

        path_stations = nx.shortest_path(self.transit_graph, origin_station, dict_last_station['station'],\
         weight='distance')
        path_length = nx.shortest_path_length(self.transit_graph, origin_station, dict_last_station['station'],\
         weight='distance')

        # stations of integration
        list_distinct_lines = []
        previous_lines = sorted(self.transit_graph.node[origin_station]['line'])
        list_distinct_lines.append({'station': origin_station, 'lines': previous_lines})

        for index in range(1, len(path_stations)):
            station = path_stations[index]
            previous_lines = list_distinct_lines[-1]['lines']
            current_lines = sorted(self.transit_graph.node[station]['line'])
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

        list_distinct_lines.append({'station': dict_last_station['station'], 'lines': ''})

        return {'subway_distance': path_length, 'alight_destination_distance': dict_last_station['distance'],\
         'stations': list_distinct_lines}

    def station_location_all_lines(self, origin_station, destination_location):
        list_routes = []
        # get the stations nearby destination point
        dict_line_stations_near_destination = self.stations_near_point_per_line(destination_location)

        # construct probable trips
        for line, dict_last_station in dict_line_stations_near_destination.iteritems():
            path_stations = nx.shortest_path(self.transit_graph, origin_station, dict_last_station['station'],\
             weight='distance')
            path_length = nx.shortest_path_length(self.transit_graph, origin_station, dict_last_station['station'],\
             weight='distance')

            # stations of integration
            list_distinct_lines = []
            previous_lines = sorted(self.transit_graph.node[origin_station]['line'])
            list_distinct_lines.append({'station': origin_station, 'lines': previous_lines})

            for index in range(1, len(path_stations)):
                station = path_stations[index]
                previous_lines = list_distinct_lines[-1]['lines']
                current_lines = sorted(self.transit_graph.node[station]['line'])
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

            list_distinct_lines.append({'station': dict_last_station['station'], 'lines': ''})

            list_routes.append({'subway_distance': path_length, 'walking_distance': dict_last_station['distance'],\
             'stations': list_distinct_lines})

        return list_routes

    def location_location_all_lines(self, origin_location, destination_location):
        list_routes = []
        ## get the stations nearby destination point
        dict_line_stations_near_origin = self.stations_near_point_per_line(origin_location)
        dict_line_stations_near_destination = self.stations_near_point_per_line(destination_location)

        # construct probable trips
        for line_origin, dict_station_origin in dict_line_stations_near_origin.iteritems():
            for line_destination, dict_station_destination in dict_line_stations_near_destination.iteritems():
                origin_station = dict_station_origin['station']
                destination_station = dict_station_destination['station']

                # get path and distance between first boaring and last alight
                path_stations = nx.shortest_path(self.transit_graph, origin_station,\
                 dict_station_destination['station'], weight='distance')
                path_length = nx.shortest_path_length(self.transit_graph, destination_station,\
                 dict_station_destination['station'], weight='distance')

                # stations of integration
                list_distinct_lines = []
                previous_lines = sorted(self.transit_graph.node[origin_station]['line'])
                list_distinct_lines.append({'station': origin_station, 'lines': previous_lines})

                for index in range(1, len(path_stations)):
                    station = path_stations[index]
                    previous_lines = list_distinct_lines[-1]['lines']
                    current_lines = sorted(self.transit_graph.node[station]['line'])
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

                list_routes.append({'walking_distance_origin': dict_station_origin['distance'],\
                 'first_station': dict_station_origin['station'],\
                 'first_line': line_origin, 'boardings': list_distinct_lines,\
                 'subway_distance': path_length,\
                 'walking_distance_destination': dict_station_destination['distance'],\
                 'last_station': dict_station_destination['station'],\
                 'last line': line_destination})

        return list_routes

    def travel_distance_shortest_walk_distance(self, first_subway_boarding, ct_origin,\
        ct_destination, boro_origin, boro_destination):

        gs_origin = self.gdf_census_tract[self.gdf_census_tract['ct2010'] == ct_origin]
        gs_origin = gs_origin[gs_origin['boro_code'] == boro_origin]
        origin_centroid = gs_origin.centroid

        # discover which was the alight station
        ## get the centroid of the census tract
        gs_destination = self.gdf_census_tract[self.gdf_census_tract['ct2010'] == ct_destination]
        gs_destination = gs_destination[gs_destination['boro_code'] == boro_destination]
        destination_centroid = gs_destination.centroid

        # compute the distance from origin to boarding station
        initial_walking_distance = vincenty((origin_centroid.iloc[0].x, origin_centroid.iloc[0].y),\
         self.transit_graph.node[first_subway_boarding]['posxy']).meters

        travel = self.station_location_shortest_walk_distance(first_subway_boarding, destination_centroid)
        #travel = self.station_location_all_lines(first_subway_boarding, destination_centroid)
        #travel = self.location_location_all_lines(origin_centroid, destination_centroid)

        travel['origin_boarding_distance'] = initial_walking_distance
        travel['boardings'] = len(travel['stations'])-1
        del travel['stations']

        return travel

'''
    Test area
'''
# transit_graph = create_transit_graph(nx.Graph(), self.gdf_stations, gdf_links)
#transit_graph = create_transit_graph(nx.MultiGraph(), self.gdf_stations, df_links)
#split_line_route(self.gdf_stations, gdf_lines, df_links)

stations_path = argv[1]
links_path = argv[2]
census_tract_path = argv[3]
result_path = argv[4]

first_subway_boarding = 49
ct_origin = '012600'
boro_origin = '1'
ct_destination = '024100'
boro_destination = '2'

t_graph = TransitGraph(stations_path, links_path, census_tract_path)
travel = t_graph.travel_distance_shortest_walk_distance(first_subway_boarding, ct_origin,\
    ct_destination, boro_origin, boro_destination)

print travel
# travel = travel_distance_shortest_walk_distance(first_subway_boarding, ct_origin,\
#     ct_destination, boro_origin, boro_destination)
#
# print travel

#plot_path(transit_graph, trip_path, result_path+'passenger_path.pdf')
# plot_complete_route(gs_origin, gs_destination, trip_path, transit_graph,\
#  trunk_colors, self.gdf_census_tract, result_path+'ct_od.png')

# dict_trip_trunks = dict()
# for trunk, destination_station in trunk_stations.iteritems():
#     print trunk, destination_station
#     trip_path = nx.dijkstra_path(transit_graph, first_subway_boarding, destination_station['station'],\
#      weight='distance')
#     dict_trip_trunks[trunk] = trip_path
#     print trip_path
#     print ''
