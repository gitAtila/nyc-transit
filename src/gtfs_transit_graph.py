
from sys import argv
import pandas as pd
import networkx as nx
import gtfs_processing as gp

class GtfsTransitGraph:

    def __init__(self, gtfs_links_path, gtfs_path):
        self.df_transit_links = pd.read_csv(gtfs_links_path)
        self.transit_feed = gp.TransitFeedProcessing(gtfs_path)
        self.gdf_stations = self.transit_feed.stops_to_shapefile()
        self.df_stop_times = self.transit_feed.stop_times()
        self.df_transfers = self.transit_feed.transfers()
        self.transit_graph = self.create_transit_graph()

    def create_transit_graph(self):
        transit_graph = nx.Graph()
        # add links to subway transit_graph
        for index, link in self.df_transit_links.iterrows():
            # add stations
            if link['from_parent_station'] not in transit_graph.nodes():
                transit_graph.add_node(link['from_parent_station'], attr_dict={'routes':[link['route_id']]})
            else:
                node_attr = nx.get_node_attributes(transit_graph, 'routes')[link['from_parent_station']]
                # append new route
                if link['route_id'] not in node_attr:
                    node_attr.append(link['route_id'])
                    transit_graph.add_node(link['from_parent_station'], routes=node_attr)

            if link['to_parent_station'] not in transit_graph.nodes():
                transit_graph.add_node(link['to_parent_station'], attr_dict={'routes':[link['route_id']]})
            else:
                node_attr = nx.get_node_attributes(transit_graph, 'routes')[link['to_parent_station']]
                # append new route
                if link['route_id'] not in node_attr:
                    node_attr.append(link['route_id'])
                    transit_graph.add_node(link['to_parent_station'], routes=node_attr)

            transit_graph.add_edge(link['from_parent_station'], link['to_parent_station'],\
             distance=link['shape_len'])

        # add transfers
        for index, transference in self.df_transfers.iterrows():
            if transference['from_stop_id'] != transference['to_stop_id']:
                transit_graph.add_edge(transference['from_stop_id'], transference['to_stop_id'],\
                 distance=0)

        return transit_graph
