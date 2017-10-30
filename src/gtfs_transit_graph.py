
from sys import argv
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
        for index, link in self.transit_links.iterrows():
            if link['from_parent_station'] not in transit_graph.nodes():
                self.transit_graph.add_node(link['from_parent_station'], attr_dict={'routes':[link['route_id']]})
            else:
                routes = self.transit_graph.nodes(data=True)[link['from_parent_station']]['routes']
                self.transit_graph.add_node(link['from_parent_station'], routes=[link['route_id']])

            transit_graph.add_edge(link['from_parent_station'], link['to_parent_station'],\
             distance=link['shape_len'])
        # add transfers
        for index, transference in self.df_transfers.iterrows():
            if transference['from_stop_id'] != transference['to_stop_id']:
                transit_graph.add_edge(transference['from_stop_id'], transference['to_stop_id'],\
                 distance=0, route='T')

        return transit_graph

gtfs_path = argv[1]
gtg = GtfsTransitGraph(gtfs_path)

#print df_nyc_subway_links
