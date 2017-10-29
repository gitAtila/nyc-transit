
from sys import argv
import networkx as nx
import gtfs_processing as gp

class GtfsTransitGraph:

    def __init__(self, gtfs_path):
        self.transit_feed = gp.TransitFeedProcessing(gtfs_path)
        self.transit_links = self.transit_feed.distinct_links_between_stations()
        self.gdf_stations = self.transit_feed.stops_to_shapefile()
        # self.dict_station_routes = self.transit_feed.distinct_route_each_station()
        # for station, list_route in self.dict_station_routes.iteritems():
        #     print station, list_route
        self.transit_graph = self.create_transit_graph()

    def create_transit_graph(self):
        transit_graph = nx.Graph()
        # add stations to subway transit_graph
        for index, station in self.gdf_stations.iterrows():
            #lines = self.dict_station_routes[station['stop_id']]
            transit_graph.add_node(station['stop_id'], name=station['stop_name'],\
             posxy=(station['geometry'].x, station['geometry'].y))

        # add links to subway transit_graph
        for index, link in self.transit_links.iterrows():
            if link['from_parent_station'] in transit_graph.nodes()\
             and link['to_parent_station'] in transit_graph.nodes():
                # compute link distance
                transit_graph.add_edge(link['from_parent_station'], link['to_parent_station'],\
                 distance=link['shape_dist_traveled'])
            else:
            	print link['from_parent_station'] + 'and' + link['to_parent_station']\
                 + 'are not present in transit_graph'

        return transit_graph

gtfs_path = argv[1]
gtg = GtfsTransitGraph(gtfs_path)

#print df_nyc_subway_links
