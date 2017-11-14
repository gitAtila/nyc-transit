'''
    Match taxi and subway passenger trips
'''
from sys import argv, path
import os
path.insert(0, os.path.abspath("../subway_trip_planner"))

import pandas as pd
import geopandas as gpd
from geopy.distance import vincenty
from datetime import datetime, timedelta
import gtfs_processing as gp

trips_position_time_path = argv[1]
sbwy_passenger_trips_path = argv[2]
sbwy_gtfs_path = argv[3]
sbwy_trip_times_path = argv[4]

origin_boarding_times_path = argv[5]
alighting_destination_times_path = argv[6]

day_type = argv[7]

computed_taxi_passenger_routes_path = argv[8]

# reconstruct passenger_route
def reconstruct_passenger_route(df_sbwy_passenger_trips, df_stop_times):
    list_passenger_trip_id = set(df_sbwy_passenger_trips['sampn_perno_tripno'].tolist())
    dict_passenger_routes = dict()
    for passenger_trip_id in list_passenger_trip_id:
        df_sbwy_passenger_route = df_sbwy_passenger_trips[df_sbwy_passenger_trips['sampn_perno_tripno'] == passenger_trip_id]
        df_sbwy_passenger_route = df_sbwy_passenger_route.sort_values('trip_sequence')

        list_passenger_trips = []
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
            list_passenger_trips.append(sorted(list_passenger_trip, key=lambda stop: stop['stop_sequence']))

        dict_passenger_routes[passenger_trip_id] = list_passenger_trips

    return dict_passenger_routes

def trip_from_sampn_perno_tripno(df_trips, sampn_perno_tripno):
    sampn_perno_tripno = sampn_perno_tripno.split('_')
    informed_trip = df_trips[(df_trips['sampn'] == int(sampn_perno_tripno[0]))\
     & (df_trips['perno'] == int(sampn_perno_tripno[1]))\
     & (df_trips['tripno'] == int(sampn_perno_tripno[2]))]
    return informed_trip

def spatial_temporal_route(origin_time, total_distance, total_duration, linestring):
    list_position_time = []

    sum_distance = 0
    previous_pos = linestring.coords[0]
    for index in range(1, len(linestring.coords)):
         current_pos = linestring.coords[index]
         distance = vincenty((previous_pos[0], previous_pos[1]), (current_pos[0], current_pos[1])).meters
         sum_distance += distance
         previous_pos = current_pos
    total_distance = sum_distance

    average_speed = total_distance/total_duration
    previous_pos = linestring.coords[0]
    previous_time = origin_time
    sum_distance = 0
    list_position_time.append({'date_time': previous_time, 'position': previous_pos})
    for index in range(1, len(linestring.coords)):
         current_pos = linestring.coords[index]
         distance = vincenty((previous_pos[0], previous_pos[1]), (current_pos[0], current_pos[1])).meters
         sum_distance += distance
         time_interval = distance/average_speed
         current_time = previous_time + timedelta(seconds=time_interval)
         list_position_time.append({'date_time': current_time, 'position': current_pos})
         previous_pos = current_pos
         previous_time = current_time
    return list_position_time

def combine_walking_subway_route(list_sbwy_trip_route, list_st_origin_walking,\
list_st_destination_walking, df_stops):
    list_sbwy_complete_route = []
    for pos_time in list_st_origin_walking:
        list_sbwy_complete_route.append({'position': pos_time['position'], 'date_time': pos_time['date_time'], 'stop_id': ''})
    for list_stop in list_sbwy_trip_route:
        for stop in list_stop:
            stop_data = df_stops[df_stops['stop_id'] == stop['stop_id']].iloc[0]
            position = (stop_data['stop_lon'], stop_data['stop_lat'])
            list_sbwy_complete_route.append({'position': position, 'date_time': stop['departure_time'],\
            'stop_id': stop['stop_id']})
    for pos_time in list_st_destination_walking:
        list_sbwy_complete_route.append({'position': pos_time['position'], 'date_time': pos_time['date_time'], 'stop_id': ''})

    return list_sbwy_complete_route

def time_overlaped_routes(list_st_taxi_route, list_sbwy_complete_route):

    taxi_first_index = 0
    sbwy_frist_index = 0
    # taxi stats first

    print list_st_taxi_route[0]['date_time'], list_sbwy_complete_route[0]['date_time']
    if list_st_taxi_route[0]['date_time'] < list_sbwy_complete_route[0]['date_time']:
        for index in range(1, len(list_st_taxi_route)):
            if list_st_taxi_route[index]['date_time'] >= list_sbwy_complete_route[0]['date_time']:
                taxi_frist_index = index
                break
    else: # sbwy starts first
        for index in range(1, len(list_sbwy_complete_route)):
            if list_sbwy_complete_route[index]['date_time'] >= list_st_taxi_route[0]['date_time']:
                sbwy_first_index = index
                break

    taxi_last_index = len(list_st_taxi_route)-1
    sbwy_last_index = len(list_sbwy_complete_route)-1
    # taxi fineshed first
    if list_st_taxi_route[-1]['date_time'] < list_sbwy_complete_route[-1]['date_time']:
        for index in range(len(list_sbwy_complete_route)):
            if list_sbwy_complete_route[index]['date_time'] <= list_st_taxi_route[-1]['date_time']:
                sbwy_last_index = index
            else:
                break
    else: #sbwy ends first
        for index in range(len(list_st_taxi_route)):
            if list_st_taxi_route[index]['date_time'] <= list_sbwy_complete_route[-1]['date_time']:
                taxi_last_index = index
            else:
                break
    print taxi_first_index, taxi_last_index, sbwy_first_index, sbwy_last_index

# read trips
df_trips = pd.read_csv(trips_position_time_path)
df_trips = df_trips[(df_trips['MODE_G10'] == 1)|(df_trips['MODE_G10'] == 7)]
df_trips['date_time_origin'] = pd.to_datetime(df_trips['date_time_origin'])
df_trips['date_time_destination'] = pd.to_datetime(df_trips['date_time_destination'])

# read gtfs
sbwy_feed = gp.TransitFeedProcessing(sbwy_gtfs_path, sbwy_trip_times_path, int(day_type))
# read subway passenger trips
df_sbwy_passenger_trips = pd.read_csv(sbwy_passenger_trips_path)

df_stop_times = sbwy_feed.get_stop_times()
df_stops = sbwy_feed.get_stops()

# filter used subway trips
list_gtfs_trip_id = list(set(df_sbwy_passenger_trips['gtfs_trip_id'].tolist()))
df_stop_times = df_stop_times[df_stop_times['trip_id'].isin(list_gtfs_trip_id)]
#print df_stop_times

dict_sbwy_passenger_routes = reconstruct_passenger_route(df_sbwy_passenger_trips, df_stop_times)

# read walking distances
gdf_origin_boarding_walking = gpd.read_file(origin_boarding_times_path)
gdf_alighting_destination_walking = gpd.read_file(alighting_destination_times_path)

# read taxi passenger trips
gdf_computed_taxi_passenger_routes = gpd.read_file(computed_taxi_passenger_routes_path)

# match routes
# iterating over taxi passenger routes
count_iterations = 0
count_overlaped = 0
for index, computed_taxi_passenger_route in gdf_computed_taxi_passenger_routes.iterrows():
    taxi_sampn_perno_tripno = computed_taxi_passenger_route['sampn_pern']
    #print 'Taxi trip', taxi_sampn_perno_tripno

    informed_taxi_trip = trip_from_sampn_perno_tripno(df_trips, taxi_sampn_perno_tripno)
    informed_taxi_pickup_time = informed_taxi_trip['date_time_origin'].iloc[0]
    informed_taxi_dropoff_time = informed_taxi_trip['date_time_destination'].iloc[0]

    computed_trip_duration = computed_taxi_passenger_route['duration']
    computed_taxi_passenger_dropoff_time = informed_taxi_pickup_time + timedelta(seconds=computed_trip_duration)

    # iterating over subway passenger routes
    for sbwy_sampn_perno_tripno, list_sbwy_trip_route in dict_sbwy_passenger_routes.iteritems():
        count_iterations += 1
        #print 'subway trip', sbwy_sampn_perno_tripno
        informed_sbwy_trip = trip_from_sampn_perno_tripno(df_trips, sbwy_sampn_perno_tripno)

        informed_sbwy_origin_time = informed_sbwy_trip['date_time_origin'].iloc[0]
        informed_sbwy_destination_time = informed_sbwy_trip['date_time_destination'].iloc[0]

        computed_sbwy_alighting_time = datetime.combine(informed_sbwy_destination_time.date(),\
        list_sbwy_trip_route[-1][-1]['departure_time'])

        # compute walking duration
        origin_boarding_walking = gdf_origin_boarding_walking[gdf_origin_boarding_walking['sampn_pern'] == sbwy_sampn_perno_tripno]
        origin_boarding_duration = float(origin_boarding_walking['duration'].iloc[0])

        alighting_destination_walking = gdf_alighting_destination_walking[gdf_alighting_destination_walking['sampn_pern'] == sbwy_sampn_perno_tripno]
        alighting_destination_duration = float(alighting_destination_walking['duration'].iloc[0])

        walking_route_duration = (origin_boarding_duration + alighting_destination_duration)/60

        computed_sbwy_destination_time = computed_sbwy_alighting_time + timedelta(minutes=walking_route_duration)

        if computed_sbwy_destination_time < informed_sbwy_origin_time:
            computed_sbwy_destination_time += timedelta(day=1)

        # verify if taxi route and subway route overlap each other temporally
        if informed_sbwy_origin_time < computed_taxi_passenger_dropoff_time\
        and informed_taxi_pickup_time < computed_sbwy_destination_time:
            count_overlaped += 1
            print 'Overlaping routes'
            print 'Taxi trip', taxi_sampn_perno_tripno
            print informed_taxi_pickup_time
            print computed_taxi_passenger_dropoff_time
            print 'Subway trip', sbwy_sampn_perno_tripno
            print informed_sbwy_origin_time
            print computed_sbwy_destination_time
            print '============================='

            # verify if taxi route and subway route overlap each other spatially
            print 'computed_taxi_passenger_route'
            print computed_taxi_passenger_route
            list_st_taxi_route = spatial_temporal_route(informed_taxi_pickup_time,\
            computed_taxi_passenger_route['distance'], computed_taxi_passenger_route['duration'],\
            computed_taxi_passenger_route['geometry'])
            print list_st_taxi_route

            print 'computed_sbwy_passenger_route'
            print list_sbwy_trip_route

            print 'computed_walking_route'
            print origin_boarding_walking
            list_st_origin_walking = spatial_temporal_route(informed_sbwy_origin_time,\
            origin_boarding_walking['distance'].iloc[0], origin_boarding_walking['duration'].iloc[0],\
            origin_boarding_walking['geometry'].iloc[0])
            #print list_st_origin_walking

            print alighting_destination_walking
            list_st_destination_walking = spatial_temporal_route(computed_sbwy_alighting_time,\
            alighting_destination_walking['distance'].iloc[0], alighting_destination_walking['duration'].iloc[0],\
            alighting_destination_walking['geometry'].iloc[0])
            #print list_st_destination_walking

            list_sbwy_complete_route = combine_walking_subway_route(list_sbwy_trip_route,\
            list_st_origin_walking, list_st_destination_walking, df_stops)
            print list_sbwy_trip_route
            
            time_overlaped_routes(list_st_taxi_route, list_sbwy_complete_route)


            stop

    #print ''
        #print list_sbwy_trip_route
        #break
    #break
print 'gdf_computed_taxi_passenger_routes', len(gdf_computed_taxi_passenger_routes)
print 'dict_sbwy_passenger_routes', len(dict_sbwy_passenger_routes)
print 'count_iterations', count_iterations
print 'count_overlaped', count_overlaped
