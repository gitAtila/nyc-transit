
from sys import argv
import pandas as pd
import networkx as nx
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
                transit_graph.add_node(link['from_parent_station'], attr_dict={'routes':[link['route_id']],\
                 'posxy':(stop['stop_lon'].iloc[0], stop['stop_lat'].iloc[0])})
            else:
                list_routes = nx.get_node_attributes(transit_graph, 'routes')[link['from_parent_station']]
                posxy = nx.get_node_attributes(transit_graph, 'posxy')[link['from_parent_station']]
                if link['route_id'] not in list_routes:
                    list_routes.append(link['route_id'])
                    transit_graph[link['from_parent_station']].update(attr_dict={'routes':list_routes,\
                     'posxy':posxy})

            if link['to_parent_station'] not in transit_graph.nodes():
                stop = df_stops[df_stops['stop_id'] == link['to_parent_station']]
                transit_graph.add_node(link['to_parent_station'], attr_dict={'routes':[link['route_id']],\
                 'posxy':(stop['stop_lon'].iloc[0], stop['stop_lat'].iloc[0])})
            else:
                list_routes = nx.get_node_attributes(transit_graph, 'routes')[link['to_parent_station']]
                posxy = nx.get_node_attributes(transit_graph, 'posxy')[link['to_parent_station']]
                if link['route_id'] not in list_routes:
                    list_routes.append(link['route_id'])
                    transit_graph[link['to_parent_station']].update(attr_dict={'routes':list_routes,\
                     'posxy':posxy})

            transit_graph.add_edge(link['from_parent_station'], link['to_parent_station'],\
             distance=link['shape_len'])
            
        # add transfers
        df_transfers = self.transit_feed.transfers()
        for index, transference in df_transfers.iterrows():
            if transference['from_stop_id'] != transference['to_stop_id']:
                transit_graph.add_edge(transference['from_stop_id'], transference['to_stop_id'],\
                 distance=0)

        return transit_graph
