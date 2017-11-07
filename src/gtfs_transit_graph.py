
from sys import argv, maxint
import pandas as pd
import networkx as nx
from datetime import datetime, timedelta
from geopy.distance import vincenty

import gtfs_processing as gp

class GtfsTransitGraph:

    def __init__(self, gtfs_links_path, gtfs_path,trip_times_path, day_type):
        self.df_transit_links = pd.read_csv(gtfs_links_path)
        self.transit_feed = gp.TransitFeedProcessing(gtfs_path, trip_times_path, day_type)
        self.transit_graph = self.create_transit_graph()

    def create_transit_graph2(self):
        transit_graph = nx.Graph()
        df_stops = self.transit_feed.get_stops()
        df_parent_stations = df_stops[df_stops['location_type'] == 1]

        for index, parent_station in df_parent_stations.iterrows():
            dict_stop_attr = dict()
            dict_stop_attr['parent_station_id'] = parent_station['stop_id']
            dict_stop_attr['parent_station_name'] = parent_station['stop_name']
            dict_stop_attr['posxy'] = (parent_station['stop_lon'], parent_station['stop_lat'])
            print dict_stop_attr
            dict_time_tables = self.transit_feed.stop_timetables(parent_station['stop_id'])
            print dict_time_tables.keys()

            # add new stations with its routes and positions
            transit_graph.add_node(parent_station['stop_id'], {'routes': dict_time_tables.keys(),\
             'posxy':(parent_station['stop_lon'], parent_station['stop_lat']),\
             'timetables':dict_time_tables})

        # add links to subway transit_graph
        for index, link in self.df_transit_links.iterrows():
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

    def unique_node_values(self, active_graph, node_key):
        list_values = []
        for index in active_graph:
            value = active_graph.node[index][node_key]
            if type(value) != list:
                if value not in list_values:
                    list_values.append(value)
            else:
                for item in value:
                    if item not in list_values:
                        list_values.append(item)
        return list_values

    def subgraph_node(self,active_graph, node_key, node_value):
        list_node = []
        for key, dict_attribute in active_graph.nodes_iter(data=True):
            if type(dict_attribute[node_key]) == list:
                if node_value in dict_attribute[node_key]:
                    list_node.append(key)
            elif dict_attribute[node_key] == node_value:
                list_node.append(key)
        subgraph = active_graph.subgraph(list_node)
        return subgraph

    def subgraph_routes_active(self, active_graph, list_route):
        list_node = []
        for key, dict_attribute in active_graph.nodes_iter(data=True):
            if type(dict_attribute['routes']) == list:
                for route in list_route:
                    if route in dict_attribute['routes']:
                        list_node.append(key)
            elif dict_attribute['routes'] == node_value:
                for route in list_route:
                    list_node.append(key)
        subgraph = active_graph.subgraph(list_node)
        return subgraph

    def subgraph_active_stops_routes(self, active_graph, list_route, date_time):
        list_active_stops = []
        for route in list_route:
            list_active_stops += self.transit_feed.active_stops_route(date_time, route)
        list_active_stops = list(set(list_active_stops))
        subgraph = active_graph.subgraph(list_active_stops)
        return subgraph

    def subgraph_active_stops(self, time):
        list_active_stops = self.transit_feed.active_stops(time)
        subgraph = self.transit_graph.subgraph(list_active_stops)
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

    def stations_near_point_per_route(self, active_graph, destination_location):
        list_trunk_stations = list()
        list_unique_routes = self.unique_node_values(active_graph, 'routes')

        # Find the nearest station from point for each route
        dict_stations_route = dict()
        for route in list_unique_routes:
            # consider only stations that are working at that moment
            #g_route = self.subgraph_active_stops_routes([route], date_time)
            subgraph_route = self.subgraph_node(active_graph, 'routes', route)
            # get the nearest station
            shortest_distance = maxint
            best_station = -1
            for node_key, dict_attribute in subgraph_route.nodes_iter(data=True):
                distance =  self.distance_points(dict_attribute['posxy'],\
                 (destination_location.iloc[0].x, destination_location.iloc[0].y))
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

    def trips_from_stations_path(self, active_graph, path_stations):

        # firstly, check if the first boarding and the last alight belongs to the same trip
        first_routes = active_graph.node[path_stations[0]]['routes']
        last_routes = active_graph.node[path_stations[-1]]['routes']
        intersection_routes = list(set(first_routes) & set(last_routes))
        if len(intersection_routes) > 0:
            list_passenger_trip = [{'boarding': {'station':path_stations[0], 'routes':intersection_routes},\
                    'alighting': {'station':path_stations[-1], 'routes':intersection_routes}}]
            return list_passenger_trip

        # stations of integration
        list_passenger_trip = []
        previous_routes = first_routes
        # print previous_routes
        traveling_routes = previous_routes
        list_passenger_trip.append({'boarding': {'station':path_stations[0], 'routes':previous_routes}})
        for index in range(1, len(path_stations)):
            current_routes = active_graph.node[path_stations[index]]['routes']

            intersection_traveling_current_routes = list(set(traveling_routes) & set(current_routes))
            intersection_last_current_routes = list(set(last_routes) & set(current_routes))

            # jump to the last station
            if len(intersection_last_current_routes) > 0:# and len(intersection_last_traveling_routes) == 0:
                # update boarding routes
                previous_boarding_routes = list_passenger_trip[-1]['boarding']['routes']
                intersection_boarding_previous_routes = list(set(previous_boarding_routes) & set(previous_routes))
                list_passenger_trip[-1]['boarding']['routes'] = intersection_boarding_previous_routes

                # add alight
                if len(intersection_traveling_current_routes) > 0:
                    list_passenger_trip[-1]['alighting'] = {'station': path_stations[index],\
                     'routes':traveling_routes}
                else:
                    list_passenger_trip[-1]['alighting'] = {'station': path_stations[index-1],\
                     'routes':traveling_routes}

                # add new boarding
                list_passenger_trip.append({'boarding': {'station':path_stations[index],\
                 'routes':intersection_last_current_routes}})
                previous_routes = current_routes
                break

            # there are transfers
            if len(intersection_traveling_current_routes) == 0:

                # update boarding routes
                previous_boarding_routes = list_passenger_trip[-1]['boarding']['routes']
                intersection_boarding_previous_routes = list(set(previous_boarding_routes) & set(previous_routes))
                list_passenger_trip[-1]['boarding']['routes'] = intersection_boarding_previous_routes

                # insert alight station
                list_passenger_trip[-1]['alighting'] = {'station':path_stations[index-1],\
                 'routes':intersection_boarding_previous_routes}

                # insert new boarding
                # transfer could happen on the previous station
                intersection_current_previus_routes = list(set(current_routes) & set(previous_routes))
                if len(intersection_current_previus_routes) > 0 and intersection_current_previus_routes in traveling_routes:
                    list_passenger_trip.append({'boarding': {'station':path_stations[index-1],\
                     'routes':intersection_current_previus_routes}})
                    traveling_routes = intersection_current_previus_routes
                else:
                    list_passenger_trip.append({'boarding': {'station':path_stations[index], 'routes':current_routes}})
                    traveling_routes = current_routes
            else:
                traveling_routes = intersection_traveling_current_routes

            previous_routes = current_routes
        # insert the last alighting
        previous_boarding_station = list_passenger_trip[-1]['boarding']['station']
        previous_boarding_routes = list_passenger_trip[-1]['boarding']['routes']
        boarding_routes = list(set(previous_boarding_routes) & set(previous_routes))
        if len(boarding_routes) > 0:
            list_passenger_trip[-1]['boarding'] = {'station':previous_boarding_station, 'routes':boarding_routes}
            list_passenger_trip[-1]['alighting'] = {'station':path_stations[-1], 'routes':boarding_routes}
        else:
            print 'Error: There is not intersection between last boarding station and last station.'

        # remove unnecessary trips
        # dict_first_occurrence = dict()
        # for trip_index in range(len(list_passenger_trip)):
        #     trip_routes = list_passenger_trip[trip_index]['boarding']['routes']
        #     # add new routes to dict
        #     for route in trip_routes:
        #         if route not in dict_first_occurrence.keys():
        #             dict_first_occurrence[route] = trip_index
        #         else:
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

    def shortest_path_n_transfers(self, active_graph, origin_station, destination_station, number_of_transfers,\
     date_time_origin):
        print 'number_of_transfers', number_of_transfers

        path_stations = []
        if number_of_transfers == 0:
            # create a graph with boarding routes and with active stops for each route
            list_boarding_routes = active_graph.node[origin_station]['routes']
            subgraph_routes = self.subgraph_active_stops_routes(active_graph, list_boarding_routes, date_time_origin)
            #subgraph_routes = self.subgraph_routes_active(active_graph, list_boarding_routes)
            try:
                path_stations = nx.shortest_path(subgraph_routes, origin_station, destination_station)
            except (nx.exception.NetworkXNoPath, nx.exception.NetworkXError) as e:
                path_stations = []
            return path_stations
        if number_of_transfers == 1:
            # create a graph with boarding and alighting routes and find the shortest path
            list_boarding_routes = active_graph.node[origin_station]['routes']
            list_alighting_routes = active_graph.node[destination_station]['routes']
            list_routes = set(list_boarding_routes + list_alighting_routes)
            print list_boarding_routes, list_alighting_routes, list_routes
            subgraph_routes = self.subgraph_active_stops_routes(active_graph, list_routes, date_time_origin)
            #subgraph_routes = self.subgraph_routes_active(active_graph, list_routes)
            try:
                path_stations = nx.shortest_path(subgraph_routes, origin_station, destination_station)
            except (nx.exception.NetworkXNoPath, nx.exception.NetworkXError) as e:
                path_stations = []

            return path_stations
        else:
            # create a graph with boarding and alighting stations route
            list_boarding_routes = active_graph.node[origin_station]['routes']
            list_alighting_routes = active_graph.node[destination_station]['routes']
            list_board_alight_routes = set(list_boarding_routes + list_alighting_routes)
            #print 'list_board_alight_routes', list_board_alight_routes

            # get unique route values
            list_unique_routes = set(self.unique_node_values(active_graph, 'routes'))

            # remove boarding and alighting ones
            list_unique_routes = list_unique_routes - list_board_alight_routes
            print list_unique_routes

            # for each route that is not in boarding and alighting stations
            min_path_length = maxint
            best_route = ''
            for new_route in list_unique_routes:
                # add this route and find the shortest path
                list_routes = list(list_board_alight_routes) + [new_route]
                subgraph_routes = self.subgraph_active_stops_routes(active_graph, list_routes, date_time_origin)
                #subgraph_routes = self.subgraph_routes_active(active_graph, list_routes)
                try:
                    path_length = nx.shortest_path_length(subgraph_routes, origin_station, destination_station)
                except (nx.exception.NetworkXNoPath, nx.exception.NetworkXError) as e:
                    path_length = maxint
                if path_length < min_path_length:
                    print new_route, path_length
                    min_path_length = path_length
                    best_route = new_route

            print best_route
            list_routes = list(list_board_alight_routes) + [best_route]
            subgraph_routes = self.subgraph_active_stops_routes(active_graph, list_routes, date_time_origin)
            #subgraph_routes = self.subgraph_routes_active(active_graph, list_routes)
            try:
                path_stations = nx.shortest_path(subgraph_routes, origin_station, destination_station)
            except (nx.exception.NetworkXNoPath, nx.exception.NetworkXError) as e:
                path_stations = []

            return path_stations

    def compute_trip_time(self, list_passenger_trip, date_time_origin):

        origin_time = date_time_origin.time()
        for passenger_trip in list_passenger_trip:
            print 'origin_time', origin_time
            print passenger_trip['boarding'], passenger_trip['alighting']
            # get timestable for both stations
            dict_timestable_boarding = self.transit_feed.stop_timestable_route(passenger_trip['boarding']['station'],\
            passenger_trip['boarding']['routes'][0])
            dict_timestable_alight = self.transit_feed.stop_timestable_route(passenger_trip['alighting']['station'],\
            passenger_trip['alighting']['routes'][0])

            # find boarding and alighting common trips
            df_common_trips = pd.DataFrame()
            alighting_direction = ''
            for boarding_id in dict_timestable_boarding.keys():
                df_boarding_direction = dict_timestable_boarding[boarding_id]

                for alighting_id in dict_timestable_alight.keys():
                    df_alighting_direction = dict_timestable_alight[alighting_id]
                    df_common_trips = df_boarding_direction[df_boarding_direction['trip_id']\
                    .isin(df_alighting_direction['trip_id'].tolist())]
                    # if there is an intersection
                    if len(df_common_trips) > 0:
                        trip_id = df_common_trips['trip_id'].iloc[0]
                        boarding_time = df_common_trips['departure_time'].iloc[0]
                        alighting_time = df_alighting_direction[df_alighting_direction['trip_id'] == trip_id]['departure_time'].iloc[0]
                        # get direction with crescent order
                        if boarding_time < alighting_time:
                            alighting_direction = alighting_id
                            break
                if alighting_direction != '':
                    break
            # find the moment of boarding
            best_boarding_trip = ''
            df_common_trips = df_common_trips.sort_values(by=['departure_time'])
            for index, boarding_trip in df_common_trips.iterrows():
                if origin_time < boarding_trip['departure_time']:
                    best_boarding_trip = boarding_trip
                    break

            print best_boarding_trip
            if type(best_boarding_trip) != str:
                df_timestable_alight = dict_timestable_alight[alighting_direction]
                best_alighting_trip = df_timestable_alight[df_timestable_alight['trip_id'] == best_boarding_trip['trip_id']].iloc[0]
                print best_alighting_trip
                print best_alighting_trip.iloc[0]
                origin_time = best_alighting_trip['departure_time']
                print ''
            else:
                print 'Error: There is not any route at this time.'


    def station_location_transfers(self, origin_station, destination_location, number_subway_routes,\
        date_time_origin):

        print 'looking for active nodes...'

        active_graph = self.subgraph_active_stops(date_time_origin.time())

        # verify if origin station is in active graph
        if origin_station in active_graph.nodes():

            ## get the nearest station from destination location for each route
            dict_route_stations_near_destination = self.stations_near_point_per_route(active_graph,\
             destination_location)

            # construct probable trips
            list_route_distances = []
            for route_id, dict_station in dict_route_stations_near_destination.iteritems():
                list_route_distances.append((route_id, dict_station))
            # sort routes in the increasing order of distance
            list_route_distances = sorted(list_route_distances, key=lambda tup:tup[1]['distance'])
            list_boarding_routes = active_graph.node[origin_station]['routes']
            path_stations = []

            if number_subway_routes == 1:
                station = ''
                for route, station_distance in list_route_distances:
                    if route in list_boarding_routes:
                        station = station_distance['station']
                        break

                print 'destination_station', station
                path_stations = self.shortest_path_n_transfers(active_graph, origin_station, station, number_subway_routes-1,\
                 date_time_origin)
                if len(path_stations) == 0:
                    print 'Error: The shortest path is too far from location.'


            elif number_subway_routes > 1:
                # find the shortest path nearest to destination station
                if number_subway_routes == 2:
                    destination_pos = 0

                    # add on origin route that is the nearest to destination location
                    while True:
                        best_destination_station = list_route_distances[destination_pos][1]['station']
                        best_destination_route = list_route_distances[destination_pos][0]
                        station_graph_routes = active_graph.node[best_destination_station]['routes']

                        if best_destination_route not in list_boarding_routes and best_destination_route in station_graph_routes:
                            print 'destination_station', best_destination_station
                            path_stations = self.shortest_path_n_transfers(active_graph, origin_station, best_destination_station,\
                             number_subway_routes-1,\
                              date_time_origin)

                        destination_pos += 1
                        if len(path_stations) > 0 or destination_pos >= len(list_route_distances):
                            break
                else:
                    print 'destination_station', list_route_distances[0]
                    path_stations = self.shortest_path_n_transfers(active_graph, origin_station,\
                     list_route_distances[0][1]['station'], number_subway_routes-1,\
                      date_time_origin)

            # path must have at least two stations
            if len(path_stations) <= 1:
                print 'Error: There is not transit path.'
                return []

            print path_stations
            for station in path_stations:
                print self.transit_graph.node[station]['routes']

            list_passenger_trip = self.trips_from_stations_path(active_graph, path_stations)

            for trip in list_passenger_trip:
                if trip['boarding']['station'] == trip['alighting']['station']:
                    print 'Error: Path with orphan station.'
                    return trip

            # compute trip time
            list_passenger_trip = self.compute_trip_time(list_passenger_trip, date_time_origin)
        else:
            print 'Error: origin_station not in active_graph.'
    # gtfs_links_path = argv[1]
    # gtfs_path = argv[2]
    # trip_times_path = argv[3]
    # day_type = argv[4]
    #
    # origin_station = ''
    # destination_location = ''
    # number_subway_routes = ''
    # date_time_origin = ''
    #
    # gtg = GtfsTransitGraph(gtfs_links_path, gtfs_path,trip_times_path, day_type)
    # gtg.unique_node_values('','')
    # #gtg.compute_trip_time([{'boarding':{'routes': ['2'], 'station': '218'}, 'alighting' :{'routes': ['2'], 'station': '127'}}], '09:00:00')
