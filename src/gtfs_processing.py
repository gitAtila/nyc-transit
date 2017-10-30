'''
    Read GTFS file and plot stops and connections
'''
import zipfile
import pandas as pd
import geopandas as gpd
from geopy.distance import vincenty
from shapely.geometry import Point, LineString

class TransitFeedProcessing:

    def __init__(self, gtfs_zip_folder):
        self.gtfs_zip_folder = gtfs_zip_folder


    def read_file_in_zip(self, file_name):
        zip_file = zipfile.ZipFile(self.gtfs_zip_folder)
        df_csv = pd.read_csv(zip_file.open(file_name))
        return df_csv

    '''
        Format spatial attributes
    '''
    # strings to geometry
    def format_points(self, df_points, lon_column, lat_column):
        # Zip the coordinates into a point object and convert to a GeoDataFrame
        geometry = [Point(xy) for xy in zip(df_points[lon_column], df_points[lat_column])]
        gdf_points = gpd.GeoDataFrame(df_points, geometry=geometry)
        del gdf_points[lon_column]
        del gdf_points[lat_column]

        return gdf_points

    # group points into linestrings
    def format_shape_lines(self, df_shapes):
        # Zip the coordinates into a point object and convert to a GeoDataFrame
        gdf_points = self.format_points(df_shapes, 'shape_pt_lon', 'shape_pt_lat')

        # Aggregate these points into a lineString object
        gdf_shapes = gdf_points.groupby(['shape_id'])['geometry'].apply(lambda x: LineString(x.tolist())).reset_index()
        gdf_shapes = gpd.GeoDataFrame(gdf_shapes, geometry='geometry')
        return gdf_shapes

    def shapes_to_shapefile(self):
        df_shapes = self.read_file_in_zip('shapes.txt')
        gdf_lines = self.format_shape_lines(df_shapes)
        return gdf_lines

    def stops_to_shapefile(self):
        df_stops = self.read_file_in_zip('stops.txt')
        gdf_stops = self.format_points(df_stops, 'stop_lon', 'stop_lat')
        return gdf_stops

    def get_stop_times(self):
        return self.read_file_in_zip('stop_times.txt')

    def distinct_route_each_station(self):
        dict_stop_route = dict()
        df_stop_times = self.read_file_in_zip('stop_times.txt')
        df_trips = self.read_file_in_zip('trips.txt')
        # get distinct trip_id for each stop_id
        list_unique_stop_id = list(df_stop_times['stop_id'].unique())
        for stop_id in list_unique_stop_id:
            list_unique_trip_id = list(df_stop_times[df_stop_times['stop_id'] == stop_id]['trip_id'].unique())
            list_route_id = []
            for trip_id in list_unique_trip_id:
                route_id = df_trips[df_trips['trip_id'] == trip_id].iloc[0]
                dict_stop_route.setdefault(stop_id, []).append(route_id)
        return dict_stop_route

    '''
        Process stop times
    '''
    # from:https://stackoverflow.com/questions/34754777/shapely-split-linestrings-at-intersections-with-other-linestrings
    def cut_line_at_points(self, line, points):
        # First coords of line
        coords = list(line.coords)

        # Keep list coords where to cut (cuts = 1)
        cuts = [0] * len(coords)
        cuts[0] = 1
        cuts[-1] = 1

        # Add the coords from the points
        coords += [list(p.coords)[0] for p in points]
        cuts += [1] * len(points)

        # Calculate the distance along the line for each point
        dists = [line.project(Point(p)) for p in coords]

        # sort the coords/cuts based on the distances
        coords = [p for (d, p) in sorted(zip(dists, coords))]
        cuts = [p for (d, p) in sorted(zip(dists, cuts))]

        # generate the Lines
        lines = []
        for i in range(len(coords)-1):
            if cuts[i] == 1:
                # find next element in cuts == 1 starting from index i + 1
                j = cuts.index(1, i + 1)
                lines.append(LineString(coords[i:j+1]))

        return lines

    def distance_linestring(self, linestring):
        total_distance = 0
        previous_position = linestring.coords[0]
        for index in range(1, len(linestring.coords)):
            current_position = linestring.coords[index]
            total_distance += vincenty(previous_position, current_position).meters
            previous_position = current_position
        return total_distance

    def distinct_links_between_stations(self):
        df_stop_times = self.read_file_in_zip('stop_times.txt')
        df_trips = self.read_file_in_zip('trips.txt')

        gdf_stops = self.stops_to_shapefile()
        gdf_shapes = self.shapes_to_shapefile()
        list_distinct_links = []
        link_attributes = []

        previous_stop = df_stop_times.iloc[0]
        for index, current_stop in df_stop_times.loc[1:].iterrows():
            # edges are consecutive stations of a line
            if previous_stop['trip_id'] == current_stop['trip_id']\
             and previous_stop['stop_sequence'] == (current_stop['stop_sequence']-1):

                from_stop_id = previous_stop['stop_id']
                to_stop_id = current_stop['stop_id']
                link_id = from_stop_id + '_' + to_stop_id

                if link_id not in list_distinct_links:

                    # get positions of stops
                    from_stop = gdf_stops[gdf_stops['stop_id'] == from_stop_id]
                    to_stop = gdf_stops[gdf_stops['stop_id'] == to_stop_id]

                    # get linestring of line
                    trip_id = current_stop['trip_id']
                    s_trip = df_trips[df_trips['trip_id'] == trip_id]

                    # get parent station
                    from_parent_station = from_stop['parent_station'].iloc[0]
                    to_parent_station = to_stop['parent_station'].iloc[0]

                    link_attributes.append({'from_stop_id': from_stop_id,'to_stop_id': to_stop_id,\
                     'from_parent_station': from_parent_station, 'to_parent_station': to_parent_station,\
                     'route_id': s_trip['route_id'].iloc[0]})

                    list_distinct_links.append(link_id)

            previous_stop = current_stop

        df_edge_attributes = pd.DataFrame(link_attributes)
        return df_edge_attributes

    def links_between_stations(self):
        df_stop_times = self.read_file_in_zip('stop_times.txt')
        df_trips = self.read_file_in_zip('trips.txt')

        gdf_stops = self.stops_to_shapefile()
        gdf_shapes = self.shapes_to_shapefile()
        link_attributes = []

        previous_stop = df_stop_times.iloc[0]
        for index, current_stop in df_stop_times.loc[1:].iterrows():
            # edges are consecutive stations of a line
            if previous_stop['trip_id'] == current_stop['trip_id']\
             and previous_stop['stop_sequence'] == (current_stop['stop_sequence']-1):

                from_stop_id = previous_stop['stop_id']
                to_stop_id = current_stop['stop_id']
                trip_id = current_stop['trip_id']

                # get positions of stops
                from_stop = gdf_stops[gdf_stops['stop_id'] == from_stop_id]
                to_stop = gdf_stops[gdf_stops['stop_id'] == to_stop_id]

                # get linestring of line
                s_trip = df_trips[df_trips['trip_id'] == trip_id]
                s_line = gdf_shapes[gdf_shapes['shape_id'] == s_trip['shape_id'].iloc[0]]

                # cut linestring by stations
                link_linestring = self.cut_line_at_points(s_line['geometry'].iloc[0], [from_stop['geometry'].iloc[0],\
                 to_stop['geometry'].iloc[0]])[1]

                # get parent station
                from_parent_station = from_stop['parent_station'].iloc[0]
                to_parent_station = to_stop['parent_station'].iloc[0]

                link_distance = self.distance_linestring(link_linestring)

                link_attributes.append({'route_id': s_trip['route_id'].iloc[0], 'trip_id': trip_id,\
                 'from_stop_id': from_stop_id, 'departure_time': previous_stop['departure_time'],\
                 'to_stop_id': to_stop_id, 'arrival_time': current_stop['arrival_time'],\
                 'from_parent_station': from_parent_station, 'to_parent_station': to_parent_station,\
                 'trip_headsign': s_trip['trip_headsign'].iloc[0], 'shape_dist_traveled': link_distance})

            else: # different lines or directions
                print 'link', previous_stop['stop_id'], current_stop['stop_id']
                # break
            previous_stop = current_stop

        df_edge_attributes = pd.DataFrame(link_attributes)
        return df_edge_attributes

# df_temporal_links = temporal_links_between_stations(gtfs_zip_folder)
# print df_temporal_links
