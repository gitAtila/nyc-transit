'''
    Compare informed and computed trip duration time
'''
from sys import argv
from datetime import datetime, timedelta
import pandas as pd

import gtfs_processing as gp

sbwy_passenger_trips_path = argv[1]
sbwy_gtfs_path = argv[2]
sbwy_trip_times_path = argv[3]
day_type = argv[4]

# read gtfs
sbwy_feed = gp.TransitFeedProcessing(sbwy_gtfs_path, sbwy_trip_times_path, int(day_type))
# read subway passenger trips
df_sbwy_passenger_trips = pd.read_csv(sbwy_passenger_trips_path)

df_stop_times = sbwy_feed.get_stop_times()
# filter used subway trips
list_gtfs_trip_id = list(set(df_sbwy_passenger_trips['gtfs_trip_id'].tolist()))
df_stop_times = df_stop_times[df_stop_times['trip_id'].isin(list_gtfs_trip_id)]
#print df_stop_times

# reconstruct passenger_route
def reconstruct_passenger_route(df_sbwy_passenger_trips, df_stop_times):
    list_passenger_trip_id = set(df_sbwy_passenger_trips['sampn_perno_tripno'].tolist())
    dict_passenger_routes = dict()
    for passenger_trip_id in list_passenger_trip_id:
        df_sbwy_passenger_route = df_sbwy_passenger_trips[df_sbwy_passenger_trips['sampn_perno_tripno'] == passenger_trip_id]
        df_sbwy_passenger_route = df_sbwy_passenger_route.sort_values('trip_sequence')

        for index, passenger_trip in df_sbwy_passenger_route.iterrows():
            # select timestable of subway trip
            df_sbwy_trip = df_stop_times[df_stop_times['trip_id'] == passenger_trip['gtfs_trip_id']]
            # select times and stops of passenger boading until alight
            boarding_stop = df_sbwy_trip[df_sbwy_trip['stop_id'] == passenger_trip['boarding_stop_id']]
            alighting_stop = df_sbwy_trip[df_sbwy_trip['stop_id'] == passenger_trip['alighting_stop_id']]
            boarding_index = int(boarding_stop.index[0])
            alighting_index = int(alighting_stop.index[0])
            df_sbwy_trip = df_sbwy_trip.loc[boarding_index: alighting_index]
            # convert stop times in a list of dictionaries
            list_passenger_trip = df_sbwy_trip[['departure_time', 'stop_id', 'stop_sequence']].T.to_dict().values()
            list_passenger_trip = sorted(list_passenger_trip, key=lambda stop: stop['stop_sequence'])
            dict_passenger_routes.setdefault(passenger_trip_id, []).append(list_passenger_trip)

    return dict_passenger_routes

dict_sbwy_passenger_routes = reconstruct_passenger_route(df_sbwy_passenger_trips, df_stop_times)
list_sbwy_computed_route_duration = []
for sampn_perno_tripno, list_sbwy_trip_route in dict_sbwy_passenger_routes.iteritems():
    sbwy_origin_time = list_sbwy_trip_route[0][0]['departure_time']
    sbwy_destination_time = list_sbwy_trip_route[-1][-1]['departure_time']

    sbwy_origin_time = timedelta(hours=sbwy_origin_time.hour, minutes=sbwy_origin_time.minute,\
     seconds=sbwy_origin_time.second, microseconds=sbwy_origin_time.microsecond)
    sbwy_destination_time = timedelta(hours=sbwy_destination_time.hour, minutes=sbwy_destination_time.minute,\
     seconds=sbwy_destination_time.second, microseconds=sbwy_destination_time.microsecond)

    duration = (sbwy_destination_time - sbwy_origin_time).total_seconds()
    list_sbwy_computed_route_duration.append(duration)

print list_sbwy_computed_route_duration
