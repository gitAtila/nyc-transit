'''
    Read GTFS file and plot stops and connections
'''
import zipfile
import pandas as pd
from datetime import datetime
from collections import defaultdict
import geopandas as gpd
from geopy.distance import vincenty
from shapely.geometry import Point, LineString

class TransitFeedProcessing:

    def __init__(self, gtfs_zip_folder, trip_times_path, day_type):
        print 'Reading GTFS...'
        self.gtfs_zip_folder = gtfs_zip_folder
        #self.df_trip_times = pd.read_csv(trip_times_path)
        self.df_stops = self.stops()
        self.df_trips = self.trips()
        self.df_stop_times = self.stop_times()

        print 'Selecting weekday...'
        # read trips and stop_times acording to day type
        list_service = self.service_weekday(day_type)
        self.df_trips = self.df_trips[self.df_trips['service_id'].isin(list_service)]
        list_trip_id = list(self.df_trips['trip_id'].unique())
        self.df_stop_times = self.df_stop_times[self.df_stop_times['trip_id'].isin(list_trip_id)]
        #self.df_trip_times = self.df_trip_times[self.df_trip_times['trip_id'].isin(list_trip_id)]

        # print 'Formating trip_times...'
        # # format datetime
        # self.df_trip_times['start_time'] = pd.to_datetime(self.df_trip_times['start_time'], format='%H:%M:%S')
        # self.df_trip_times['end_time'] = pd.to_datetime(self.df_trip_times['end_time'], format='%H:%M:%S')

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

    def format_hour(self,str_time):
        try:
            formated_time = datetime.strptime(str_time, '%H:%M:%S').time()
        except ValueError:
            time = str_time.split(':')
            if int(time[0]) > 23:
                new_hour = int(time[0]) - 24
                str_time = str(new_hour) + ':' + time[1] + ':' + time[2]
                formated_time = datetime.strptime(str_time, '%H:%M:%S').time()
        return formated_time
    # set times as datetime object
    def format_stop_times(self, df_stop_times):
        list_stop_times = []
        df_stop_times['departure_time'] = df_stop_times['departure_time'].apply(self.format_hour)
        df_stop_times['arrival_time'] = df_stop_times['arrival_time'].apply(self.format_hour)
        return df_stop_times

    def geo_shape_lines(self):
        df_shapes = self.read_file_in_zip('shapes.txt')
        gdf_lines = self.format_shape_lines(df_shapes)
        return gdf_lines

    def geo_stops(self):
        df_stops = self.read_file_in_zip('stops.txt')
        gdf_stops = self.format_points(df_stops, 'stop_lon', 'stop_lat')
        return gdf_stops

    def stop_times(self):
        df_stop_times = self.read_file_in_zip('stop_times.txt')
        df_stop_times = self.format_stop_times(df_stop_times)
        return df_stop_times

    def stop_times_trip(self, trip_id):
        df_stop_times = self.read_file_in_zip('stop_times.txt')
        df_stop_times_trip = df_stop_times[df_stop_times['trip_id'] == trip_id]
        #df_stop_times_trip_id = self.format_stop_times(df_stop_times_trip_id)
        return df_stop_times_trip

    def transfers(self):
        return self.read_file_in_zip('transfers.txt')

    def stops(self):
        return self.read_file_in_zip('stops.txt')

    def get_stops(self):
        return self.df_stops

    def trips(self):
        return self.read_file_in_zip('trips.txt')

    def calendar(self):
        return self.read_file_in_zip('calendar.txt')

    def stop_timetables(self, parent_station_id):
        list_timetable = []
        dict_timetable = defaultdict(lambda: defaultdict(list))

        # get stop child stations
        df_child_stops = self.df_stops[self.df_stops['parent_station'] == parent_station_id]
        for index, child_stop in df_child_stops.iterrows():
            # get stop sequence and departure time
            child_stop_times = self.df_stop_times[self.df_stop_times['stop_id'] == child_stop['stop_id']]
            child_stop_times = child_stop_times[['trip_id', 'departure_time', 'stop_sequence']]

            # get route_id and direction name
            for index, child_stop_time in child_stop_times.iterrows():
                route_headsign = self.df_trips[self.df_trips['trip_id'] == child_stop_time['trip_id']]

                dict_timetable[route_headsign['route_id'].iloc[0]][child_stop['stop_id']]\
                .append({'stop_sequence': child_stop_time['stop_sequence'], 'trip_headsign': route_headsign['trip_headsign'].iloc[0],\
                'trip_id': child_stop_time['trip_id'], 'departure_time': child_stop_time['departure_time']})

        # convert timetable to dataframe
        for route_id, dict_child in dict_timetable.iteritems():
            for child_id, list_timetable in dict_child.iteritems():
                dict_timetable[route_id][child_id] = pd.DataFrame(list_timetable)

        return dict_timetable

    def trips_start_end_times(self, df_trips, df_stop_times):
        list_start_end_times = []
        df_stop_times = df_stop_times[['trip_id', 'departure_time']]
        for index, trip in df_trips.iterrows():
            trip_id = trip['trip_id']
            times_trip = df_stop_times[df_stop_times['trip_id'] == trip_id]
            sorted_trip_time = times_trip.sort_values(by=['departure_time'])
            start_time = sorted_trip_time.iloc[0]['departure_time']
            end_time = sorted_trip_time.iloc[-1]['departure_time']
            list_start_end_times.append({'trip_id': trip_id, 'route_id': trip['route_id'],\
            'start_time': start_time, 'end_time':end_time})
            print list_start_end_times[-1]
        return pd.DataFrame(list_start_end_times)

    def service_weekday(self, day_type):
        day_type = int(day_type)
        df_calendar = self.calendar()
        # get service_id in that weekday
        list_service_id = []
        if day_type == 1: # weekday
            for index in range(1,6):
                print index
                list_service_id += df_calendar[df_calendar.iloc[:,index] == 1]['service_id'].tolist()
            list_service_id = set(list_service_id)
        elif day_type == 2: # saturday
            list_service_id = df_calendar[df_calendar.iloc[:,6] == 1]['service_id'].tolist()
        elif day_type == 3: # sunday
            list_service_id = df_calendar[df_calendar.iloc[:,7] == 1]['service_id'].tolist()
        else:
            return None
        return list_service_id

    def distinct_route_each_station(self):
        dict_stop_route = dict()
        # df_stop_times = self.stop_times()
        # df_trips = self.trips()
        # get distinct trip_id for each stop_id
        list_unique_stop_id = list(self.df_stop_times['stop_id'].unique())
        for stop_id in list_unique_stop_id:
            list_unique_trip_id = list(self.df_stop_times[self.df_stop_times['stop_id'] == stop_id]['trip_id'].unique())
            list_route_id = []
            for trip_id in list_unique_trip_id:
                route_id = self.df_trips[self.df_trips['trip_id'] == trip_id].iloc[0]
                dict_stop_route.setdefault(stop_id, []).append(route_id)
        return dict_stop_route

    def active_stops_route(self, date_time, route):
        # trips happening at the moment
        route_trips = self.df_trip_times[self.df_trip_times['route_id'] == route]
        list_trip_id = []
        for index, start_end in route_trips.iterrows():
            start_time = start_end['start_time'].time()
            end_time = start_end['end_time'].time()
            in_time = date_time.time()
            if start_time <= end_time:
                if in_time >= start_time and in_time <= end_time:
                    list_trip_id.append(start_end['trip_id'])
                    break
            else:
                if in_time >= start_time and in_time >= end_time:
                    list_trip_id.append(start_end['trip_id'])
                    break

        list_stops = []
        for trip_id in list_trip_id:
            list_stops += self.stop_times_trip(trip_id)['stop_id'].tolist()
        list_stops = [stop_id[:-1] for stop_id in list_stops]
        return list_stops

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
        # df_stop_times = self.stop_times()
        # df_trips = self.trips()
        # df_calendar = self.calendar()
        #
        # # get service_id in that weekday
        # list_service_id = []
        # if day_type == 1: # weekday
        #     for index in range(1,6):
        #         print index
        #         list_service_id += df_calendar[df_calendar.iloc[:,index] == 1]['service_id'].tolist()
        #     list_service_id = set(list_service_id)
        # elif day_type == 2: # saturday
        #     list_service_id = df_calendar[df_calendar.iloc[:,6] == 1]['service_id'].tolist()
        # elif day_type == 3: # sunday
        #     list_service_id = df_calendar[df_calendar.iloc[:,7] == 1]['service_id'].tolist()
        # else:
        #     return None
        #
        # # filter df_trips by service_id
        # list_trip_id = list(df_trips[df_trips['service_id'].isin(list_service_id)]['trip_id'].unique())
        # # filter trips by time
        # # get stop_times in that day
        # df_stop_times = df_stop_times[df_stop_times['trip_id'].isin(list_trip_id)]

        list_distinct_links = []
        link_attributes = []

        previous_stop = self.df_stop_times.iloc[0]
        for index, current_stop in self.df_stop_times.loc[1:].iterrows():
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
                    s_trip = self.df_trips[self.df_trips['trip_id'] == trip_id]

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
        # df_stop_times = self.stop_times()
        # df_trips = self.trips

        gdf_stops = self.geo_stops()
        gdf_shapes = self.geo_shape_lines()
        link_attributes = []

        previous_stop = self.df_stop_times.iloc[0]
        for index, current_stop in self.df_stop_times.loc[1:].iterrows():
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
                s_trip = self.df_trips[self.df_trips['trip_id'] == trip_id]
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

# from sys import argv
# gtfs_zip_folder = argv[1]
# gp = TransitFeedProcessing(gtfs_zip_folder)
# df_stop_times = gp.stop_times()
#
# df_trips = gp.trips()
# df_start_end_trips = gp.trips_start_end_times(df_trips, df_stop_times)
# print df_start_end_trips
