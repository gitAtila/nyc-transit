
from sys import argv, maxint
import pandas as pd
import networkx as nx
from datetime import datetime, timedelta
from geopy.distance import vincenty

import gtfs_processing as gp

class GtfsTransitGraph:

    def __init__(self, gtfs_links_path, gtfs_path):
        self.df_transit_links = pd.read_csv(gtfs_links_path)
        self.transit_feed = gp.TransitFeedProcessing(gtfs_path)
        self.transit_graph = self.create_transit_graph()

    def create_transit_graph(self):
        transit_graph = nx.Graph()
        df_stops = self.transit_feed.stops()
        df_stops = df_stops[df_stops['location_type'] == 1]
        # add links to subway transit_graph
        for index, link in self.df_transit_links.iterrows():

            # add new stations with its routes and positions
            if link['from_parent_station'] not in transit_graph.nodes():
                # get station position
                stop = df_stops[df_stops['stop_id'] == link['from_parent_station']]
                transit_graph.add_node(link['from_parent_station'], {'routes':[link['route_id']],\
                 'posxy':(stop['stop_lon'].iloc[0], stop['stop_lat'].iloc[0])})
            else: # append routes to existing stations
                list_routes = nx.get_node_attributes(transit_graph, 'routes')[link['from_parent_station']]
                posxy = nx.get_node_attributes(transit_graph, 'posxy')[link['from_parent_station']]
                if link['route_id'] not in list_routes:
                    list_routes.append(link['route_id'])
                    transit_graph.add_node(link['from_parent_station'], {'routes':list_routes,\
                     'posxy':posxy})

            # add new stations with its routes and positions
            if link['to_parent_station'] not in transit_graph.nodes():
                stop = df_stops[df_stops['stop_id'] == link['to_parent_station']]
                transit_graph.add_node(link['to_parent_station'], {'routes':[link['route_id']],\
                 'posxy':(stop['stop_lon'].iloc[0], stop['stop_lat'].iloc[0])})
            else:  # append routes to existing stations
                list_routes = nx.get_node_attributes(transit_graph, 'routes')[link['to_parent_station']]
                posxy = nx.get_node_attributes(transit_graph, 'posxy')[link['to_parent_station']]
                if link['route_id'] not in list_routes:
                    list_routes.append(link['route_id'])
                    transit_graph.add_node(link['to_parent_station'], {'routes':list_routes,\
                     'posxy':posxy})

            # add edges with its distance to connecting stations
            transit_graph.add_edge(link['from_parent_station'], link['to_parent_station'],\
             distance=link['shape_len'])

        # add transfers between different routes
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

    def subgraph_routes(self, list_route):
        list_node = []
        for key, dict_attribute in self.transit_graph.nodes_iter(data=True):
            if type(dict_attribute['routes']) == list:
                for route in list_route:
                    if route in dict_attribute['routes']:
                        list_node.append(key)
            elif dict_attribute['routes'] == node_value:
                for route in list_route:
                    sslist_node.append(key)
        subgraph = self.transit_graph.subgraph(list_node)
        return subgraph

    def distance_points(self, point_lon_lat_A, point_lon_lat_B):
        return vincenty((point_lon_lat_A[1], point_lon_lat_A[0]),\
         (point_lon_lat_B[1], point_lon_lat_B[0])).meters

    def stations_near_point_per_route(self, gs_point):
        list_trunk_stations = list()
        list_unique_routes = self.unique_node_values('routes')

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

    def trips_from_stations_path(self, path_stations):
        # stations of integration
        list_passenger_trip = []
        previous_routes = sorted(self.transit_graph.node[path_stations[0]]['routes'])
        list_passenger_trip.append({'boarding':{'station': path_stations[0], 'routes': previous_routes}})
        for index in range(1, len(path_stations)):

            station = path_stations[index]
            previous_routes = list_passenger_trip[-1]['boarding']['routes']
            current_routes = sorted(self.transit_graph.node[station]['routes'])
            intersection_routes = sorted(list(set(previous_routes) & set(current_routes)))

            # there is an itegration
            if len(intersection_routes) == 0:
                list_passenger_trip[-1]['alighting'] = {'station': path_stations[index-1], 'routes': previous_routes}
                list_passenger_trip.append({'boarding': {'station': station, 'routes': current_routes}})

            # remove from the previous trip the routes that it is not in the current trip
            elif current_routes != previous_routes and previous_routes != intersection_routes:
                previous_routes = intersection_routes
                previous_station = list_passenger_trip[-1]['boarding']['station']
                list_passenger_trip[-1]['boarding'] = {'station': previous_station, 'routes': previous_routes}

        #append last aligth
        list_passenger_trip[-1]['alighting'] = {'station': path_stations[-1], 'routes': previous_routes}

        return list_passenger_trip

    def station_location_shortest_walk_distance(self, origin_station, destination_location):
        ## get the nearest station from destination location
        dict_route_stations_near_destination = self.stations_near_point_per_route(destination_location)
        dict_last_station = self.best_route_shortest_walk_distance(dict_route_stations_near_destination, 'route')

        path_stations = nx.shortest_path(self.transit_graph, origin_station, dict_last_station['station'],\
         weight='distance')
        path_length = nx.shortest_path_length(self.transit_graph, origin_station, dict_last_station['station'],\
         weight='distance')

        #print path_stations
        list_passenger_trip = self.trips_from_stations_path(path_stations)

        for trip in list_passenger_trip:
            print trip

        return {'subway_distance': path_length, 'alight_destination_distance': dict_last_station['distance'],\
         'stations': list_passenger_trip}

    def shortest_path_n_transfers(self, origin_station, destination_station, number_of_transfers):
        print 'number_of_transfers', number_of_transfers

        path_stations = []
        if number_of_transfers == 0:
            # create a graph with boarding routes and find the shortest path
            list_boarding_routes = self.transit_graph.node[origin_station]['routes']
            subgraph_routes = self.subgraph_routes(list_boarding_routes)
            try:
                path_stations = nx.shortest_path(subgraph_routes, origin_station, destination_station)
            except nx.exception.NetworkXNoPath:
                path_stations = []
            return path_stations
        if number_of_transfers == 1:
            # create a graph with boarding and alighting routes and find the shortest path
            list_boarding_routes = self.transit_graph.node[origin_station]['routes']
            list_alighting_routes = self.transit_graph.node[destination_station]['routes']
            list_routes = set(list_boarding_routes + list_alighting_routes)
            print list_boarding_routes, list_alighting_routes, list_routes
            subgraph_routes = self.subgraph_routes(list_routes)
            try:
                path_stations = nx.shortest_path(subgraph_routes, origin_station, destination_station)
            except nx.exception.NetworkXNoPath:
                path_stations = []
            return path_stations
        else:
            # create a graph with boarding and alighting stations route
            list_boarding_routes = self.transit_graph.node[origin_station]['routes']
            list_alighting_routes = self.transit_graph.node[destination_station]['routes']
            list_board_alight_routes = set(list_boarding_routes + list_alighting_routes)
            #print 'list_board_alight_routes', list_board_alight_routes

            # get unique route values
            list_unique_routes = set(self.unique_node_values('routes'))

            # remove boarding and alighting ones
            list_unique_routes = list_unique_routes - list_board_alight_routes
            print list_unique_routes

            # for each route that is not in boarding and alighting stations
            min_path_length = maxint
            best_route = ''
            for new_route in list_unique_routes:
                # add this route and find the shortest path
                list_routes = list(list_board_alight_routes) + [new_route]
                subgraph_routes = self.subgraph_routes(list_routes)
                try:
                    path_length = nx.shortest_path_length(subgraph_routes, origin_station, destination_station)
                except nx.exception.NetworkXNoPath:
                    path_length = maxint
                if path_length < min_path_length:
                    print new_route, path_length
                    min_path_length = path_length
                    best_route = new_route

            print best_route
            list_routes = list(list_board_alight_routes) + [best_route]

            subgraph_routes = self.subgraph_routes(list_routes)
            try:
                path_stations = nx.shortest_path(subgraph_routes, origin_station, destination_station)
            except nx.exception.NetworkXNoPath:
                path_stations = []

            return path_stations

    def compute_trip_time(self, list_passenger_trip, date_time_origin):
        df_stop_times = self.transit_feed.stop_times()
        df_trips = self.transit_feed.trips()
        df_calendar = self.transit_feed.calendar()

        # get service_id in that weekday
        list_service_id_weekday = df_calendar[df_calendar.iloc[:,1+date_time_origin.weekday()] == 1]['service_id'].tolist()
        # filter df_trips by service_id
        df_trips_weekday = df_trips[df_trips['service_id'].isin(list_service_id_weekday)]

        for trip in list_passenger_trip:
            print trip#['boarding']['route']
            # filter trips by route
            list_trip_id = list(df_trips_weekday[df_trips_weekday['route_id'] == trip['boarding']['routes'][0]]['trip_id'].unique())
            # filter stop_times by trip_id
            df_stop_times_trip_id = df_stop_times[df_stop_times['trip_id'].isin(list_trip_id)]
            # split dataframe by direction
            df_stop_times_south = df_stop_times_trip_id[df_stop_times_trip_id['stop_id'].str.contains('S')]
            df_stop_times_north = df_stop_times_trip_id[df_stop_times_trip_id['stop_id'].str.contains('N')]
            # filter stop_times by stop_id
            df_stop_times_south_boarding = df_stop_times_south[df_stop_times_south['stop_id'].str.contains(trip['boarding']['station'])]
            df_stop_times_north_boarding = df_stop_times_north[df_stop_times_north['stop_id'].str.contains(trip['boarding']['station'])]

            # find the next departure after passenger origin for both directions north and south
            df_stop_times_south_boarding = df_stop_times_south_boarding[df_stop_times_south_boarding['departure_time']\
             > date_time_origin.time()]
            s_stop_times_south_boarding = df_stop_times_south_boarding.sort_values(by=['departure_time']).iloc[0]

            df_stop_times_north_boarding = df_stop_times_north_boarding[df_stop_times_north_boarding['departure_time']\
             > date_time_origin.time()]
            s_stop_times_north_boarding = df_stop_times_north_boarding.sort_values(by=['departure_time']).iloc[0]

            print date_time_origin
            print s_stop_times_south_boarding
            print s_stop_times_north_boarding

            # find destination's direction
            df_stop_times_south_trip_id = df_stop_times_south[df_stop_times_south['trip_id'] == s_stop_times_south_boarding['trip_id']]
            df_stop_times_north_trip_id = df_stop_times_north[df_stop_times_north['trip_id'] == s_stop_times_north_boarding['trip_id']]
            print df_stop_times_south_trip_id
            print df_stop_times_north_trip_id
            print trip['alighting']['station']
            df_stop_times_south_alighting = df_stop_times_south_trip_id[df_stop_times_south_trip_id['stop_id']\
             .str.contains(trip['alighting']['station'])]
            print df_stop_times_south_alighting

            # for index, stop_times in df_stop_times_south.iterrows():
            #     print stop_times['trip_id'], stop_times['departure_time'], stop_times['stop_id']
            #     break


    def station_location_transfers(self, origin_station, destination_location, number_subway_routes, date_time_origin):

        ## get the nearest station from destination location for each route
        dict_route_stations_near_destination = self.stations_near_point_per_route(destination_location)

        # construct probable trips
        list_route_distances = []
        for key, dict_station in dict_route_stations_near_destination.iteritems():
            list_route_distances.append((key, dict_station))
        list_route_distances = sorted(list_route_distances, key=lambda tup:tup[1]['distance'])
        list_boarding_routes = self.transit_graph.node[origin_station]['routes']
        path_stations = []
        if number_subway_routes == 1:
            station = ''
            for route, station_distance in list_route_distances:
                if route in list_boarding_routes:
                    station = station_distance['station']
                    break
            print 'destination_station', station
            path_stations = self.shortest_path_n_transfers(origin_station, station, number_subway_routes-1)

        elif number_subway_routes > 1:
            # find the shortest path nearest to destination station
            if number_subway_routes == 2:
                best_destination = 0

                while True:
                    if list_route_distances[best_destination][0] not in list_boarding_routes:
                        print 'destination_station', list_route_distances[best_destination]
                        path_stations = self.shortest_path_n_transfers(origin_station,\
                         list_route_distances[best_destination][1]['station'],\
                         number_subway_routes-1)

                    best_destination += 1
                    if len(path_stations) > 0 or best_destination > len(list_route_distances):
                        #print unknown
                        break
            else:

                print 'destination_station', list_route_distances[0]
                path_stations = self.shortest_path_n_transfers(origin_station,\
                 list_route_distances[0][1]['station'],\
                 number_subway_routes-1)
                #print unknown

        if len(path_stations) == 0:
            print 'There is no path'
            return []

        print path_stations
        for station in path_stations:
            print self.transit_graph.node[station]['routes']
        list_passenger_trip = self.trips_from_stations_path(path_stations)

        # compute trip time
        list_passenger_trip = self.compute_trip_time(list_passenger_trip, date_time_origin)
