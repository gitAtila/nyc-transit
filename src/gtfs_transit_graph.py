
from sys import argv, maxint
import pandas as pd
import networkx as nx
from geopy.distance import vincenty

import gtfs_processing as gp

class GtfsTransitGraph:

    def __init__(self, gtfs_links_path, gtfs_path):
        self.df_transit_links = pd.read_csv(gtfs_links_path)
        self.transit_feed = gp.TransitFeedProcessing(gtfs_path)
        # self.df_stations = self.transit_feed.stops_to_shapefile()
        self.df_stop_times = self.transit_feed.stop_times()
        self.transit_graph = self.create_transit_graph()

    def create_transit_graph(self):
        transit_graph = nx.Graph()
        df_stops = self.transit_feed.stops()
        df_stops = df_stops[df_stops['location_type'] == 1]
        # add links to subway transit_graph
        for index, link in self.df_transit_links.iterrows():
            # add stations
            if link['from_parent_station'] not in transit_graph.nodes():
                # get station position
                stop = df_stops[df_stops['stop_id'] == link['from_parent_station']]
                transit_graph.add_node(link['from_parent_station'], {'routes':[link['route_id']],\
                 'posxy':(stop['stop_lon'].iloc[0], stop['stop_lat'].iloc[0])})
            else:
                list_routes = nx.get_node_attributes(transit_graph, 'routes')[link['from_parent_station']]
                posxy = nx.get_node_attributes(transit_graph, 'posxy')[link['from_parent_station']]
                if link['route_id'] not in list_routes:
                    list_routes.append(link['route_id'])
                    transit_graph.add_node(link['from_parent_station'], {'routes':list_routes,\
                     'posxy':posxy})
                    # transit_graph[link['from_parent_station']].update({'routes':list_routes,\
                    #  'posxy':posxy})

            if link['to_parent_station'] not in transit_graph.nodes():
                stop = df_stops[df_stops['stop_id'] == link['to_parent_station']]
                transit_graph.add_node(link['to_parent_station'], {'routes':[link['route_id']],\
                 'posxy':(stop['stop_lon'].iloc[0], stop['stop_lat'].iloc[0])})
            else:
                list_routes = nx.get_node_attributes(transit_graph, 'routes')[link['to_parent_station']]
                posxy = nx.get_node_attributes(transit_graph, 'posxy')[link['to_parent_station']]
                if link['route_id'] not in list_routes:
                    list_routes.append(link['route_id'])
                    transit_graph.add_node(link['to_parent_station'], {'routes':list_routes,\
                     'posxy':posxy})
                    # transit_graph[link['to_parent_station']].update({'routes':list_routes,\
                    #  'posxy':posxy})

            transit_graph.add_edge(link['from_parent_station'], link['to_parent_station'],\
             distance=link['shape_len'])

        # add transfers
        df_transfers = self.transit_feed.transfers()
        for index, transference in df_transfers.iterrows():
            if transference['from_stop_id'] != transference['to_stop_id']\
             and transference['from_stop_id'] in transit_graph.nodes() and transference['to_stop_id'] in transit_graph.nodes():
                from_stop = df_stops[df_stops['stop_id'] == transference['from_stop_id']]
                to_stop = df_stops[df_stops['stop_id'] == transference['to_stop_id']]

                transit_graph.add_edge(transference['from_stop_id'], transference['to_stop_id'],\
                 distance=vincenty((from_stop['stop_lon'].iloc[0], from_stop['stop_lat'].iloc[0]),\
                  (to_stop['stop_lon'].iloc[0], to_stop['stop_lat'].iloc[0])).meters)

        return transit_graph

    def unique_node_values(self, node_key):
        list_values = []
        for index in self.transit_graph:
            value = self.transit_graph.node[index][node_key]
            if type(value) != list:
                if value not in list_values:
                    list_values.append(value)
            else:
                for item in value:
                    if item not in list_values:
                        list_values.append(item)
        return list_values

    def subgraph_node(self, node_key, node_value):
        list_node = []
        for key, dict_attribute in self.transit_graph.nodes_iter(data=True):
            if type(dict_attribute[node_key]) == list:
                if node_value in dict_attribute[node_key]:
                    list_node.append(key)
            elif dict_attribute[node_key] == node_value:
                list_node.append(key)
        subgraph = self.transit_graph.subgraph(list_node)
        return subgraph

    def distance_points(self, point_lon_lat_A, point_lon_lat_B):
        return vincenty((point_lon_lat_A[1], point_lon_lat_A[0]),\
         (point_lon_lat_B[1], point_lon_lat_B[0])).meters

    def stations_near_point_per_route(self, gs_point):
        list_trunk_stations = list()
        list_unique_routes = self.unique_node_values('routes')
        #print list_unique_routes
        # Find the nearest station from point for each route
        dict_stations_route = dict()
        for route in list_unique_routes:
            g_route = self.subgraph_node('routes', route)
            # get the nearest station
            shortest_distance = maxint
            best_station = -1
            for node_key, dict_attribute in g_route.nodes_iter(data=True):
                distance =  self.distance_points(dict_attribute['posxy'], (gs_point.iloc[0].x, gs_point.iloc[0].y))
                if distance < shortest_distance:
                    shortest_distance = distance
                    best_station = node_key
            dict_stations_route[route] = {'station':best_station ,'distance': shortest_distance}
        return dict_stations_route

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
        dict_route_stations_near_destination = self.stations_near_point_per_route(destination_location)

        # construct probable trips
        dict_last_station = self.best_route_shortest_walk_distance(dict_route_stations_near_destination, 'route')

        path_stations = nx.shortest_path(self.transit_graph, origin_station, dict_last_station['station'],\
         weight='distance')
        path_length = nx.shortest_path_length(self.transit_graph, origin_station, dict_last_station['station'],\
         weight='distance')

        print path_stations

        # stations of integration
        list_distinct_routes = []
        previous_routes = sorted(self.transit_graph.node[origin_station]['routes'])
        list_distinct_routes.append({'station': origin_station, 'routes': previous_routes})

        for index in range(1, len(path_stations)):
            station = path_stations[index]
            previous_routes = list_distinct_routes[-1]['routes']
            current_routes = sorted(self.transit_graph.node[station]['routes'])
            intersection_routes = sorted(list(set(previous_routes) & set(current_routes)))

            # there is an itegration
            if len(intersection_routes) == 0:
                list_distinct_routes.append({'station': path_stations[index-1], 'routes': previous_routes})
                list_distinct_routes.append({'station': station, 'routes': current_routes})

            # remove from the previous routes the ones that is not in the current routes
            elif current_routes != previous_routes and previous_routes != intersection_routes:
                previous_routes = intersection_routes
                previous_station = list_distinct_routes[-1]['station']
                del list_distinct_routes[-1]
                list_distinct_routes.append({'station': previous_station, 'routes': previous_routes})

        list_distinct_routes.append({'station': dict_last_station['station'], 'routes': dict_last_station['route']})

        return {'subway_distance': path_length, 'alight_destination_distance': dict_last_station['distance'],\
         'stations': list_distinct_routes}
