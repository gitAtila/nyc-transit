'''
    Match taxi and subway passenger trips
'''
from sys import argv, path, maxint
import os
path.insert(0, os.path.abspath("../subway_trip_planner"))

import pandas as pd
import geopandas as gpd
from geopy.distance import vincenty
from datetime import datetime, timedelta
import gtfs_processing as gp

survey_trips_path = argv[1]
sbwy_trips_path = argv[2]
taxi_trips_path = argv[3]
result_path = argv[4]

# reconstruct passenger_route
def reconstruct_passenger_route(df_sbwy_passenger_trips, df_stop_times):
    list_passenger_trip_id = set(df_sbwy_passenger_trips['sampn_perno_tripno'].tolist())
    dict_passenger_routes = dict()

    for passenger_trip_id in list_passenger_trip_id:
        # trips of the same travel
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


def time_overlaped_routes(list_taxi_route, computed_sbwy_trip):

    taxi_first_index = 0
    sbwy_first_index = 0
    # taxi stats first

    if list_taxi_route[0]['date_time'] < computed_sbwy_trip[0]['date_time']:
        for index in range(1, len(list_taxi_route)):
            if list_taxi_route[index]['date_time'] >= computed_sbwy_trip[0]['date_time']:
                taxi_frist_index = index
                break
    else: # sbwy starts first
        for index in range(1, len(computed_sbwy_trip)):
            if computed_sbwy_trip[index]['date_time'] >= list_taxi_route[0]['date_time']:
                sbwy_first_index = index
                break

    taxi_last_index = len(list_taxi_route)-1
    sbwy_last_index = len(computed_sbwy_trip)-1
    # taxi fineshed first
    if list_taxi_route[-1]['date_time'] < computed_sbwy_trip[-1]['date_time']:
        for index in range(len(computed_sbwy_trip)):
            if computed_sbwy_trip[index]['date_time'] <= list_taxi_route[-1]['date_time']:
                sbwy_last_index = index
            else:
                break
    else: #sbwy ends first
        for index in range(len(list_taxi_route)):
            if list_taxi_route[index]['date_time'] <= computed_sbwy_trip[-1]['date_time']:
                taxi_last_index = index
            else:
                break

    overlaped_taxi_indexes = (taxi_first_index, taxi_last_index)
    overlaped_sbwy_indexes = (sbwy_first_index, sbwy_last_index)

    return overlaped_taxi_indexes, overlaped_sbwy_indexes

def integration_positions(list_taxi_trip, list_sbwy_trip):
    shortest_distance = maxint
    sbwy_integration_index = 0
    taxi_integration_index = 0
    for sbwy_pos in range(len(list_sbwy_trip)):
        for taxi_pos in range(len(list_taxi_trip)):
            distance = vincenty((list_sbwy_trip[sbwy_pos]['longitude'], list_sbwy_trip[sbwy_pos]['latitude']),\
            (list_taxi_trip[taxi_pos]['longitude'], list_taxi_trip[taxi_pos]['latitude'])).meters
            if distance < shortest_distance:
                shortest_distance = distance
                sbwy_integration_index = sbwy_pos
                taxi_integration_index = taxi_pos

    return {'shortest_distance': shortest_distance, 'sbwy_index': sbwy_integration_index,\
    'taxi_index': taxi_integration_index}

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

def add_date_time(origin_time, list_steps):
    list_position_time = []
    for step in list_steps:
        step_time = origin_time + timedelta(seconds=step['duration'])
        step['date_time'] = step_time
    return list_steps

def compute_traveling_walking_duration_distance(computed_sbwy_trip):
    walking_duration = 0
    walking_distance = 0
    traveling_duration = 0
    traveling_distance = 0

# read trips
df_trips = pd.read_csv(survey_trips_path)
df_trips = df_trips[(df_trips['MODE_G10'] == 1)|(df_trips['MODE_G10'] == 7)]
df_trips['date_time_origin'] = pd.to_datetime(df_trips['date_time_origin'])
df_trips['date_time_destination'] = pd.to_datetime(df_trips['date_time_destination'])

df_taxi_trips = pd.read_csv(taxi_trips_path)
del df_taxi_trips['id']

df_sbwy_trips = pd.read_csv(sbwy_trips_path)
del df_sbwy_trips['id']
df_sbwy_trips['date_time'] = pd.to_datetime(df_sbwy_trips['date_time'])

dict_taxi_trips = group_df_rows(df_taxi_trips, 'sampn_perno_tripno')
dict_sbwy_trips = group_df_rows(df_sbwy_trips, 'sampn_perno_tripno')

# match routes
# iterating over taxi passenger routes
list_matches = []
for taxi_sampn_perno_tripno, computed_taxi_trip in dict_taxi_trips.iteritems():

    informed_taxi_trip = trip_from_sampn_perno_tripno(df_trips, taxi_sampn_perno_tripno)
    informed_taxi_pickup_time = informed_taxi_trip['date_time_origin'].iloc[0]
    informed_taxi_dropoff_time = informed_taxi_trip['date_time_destination'].iloc[0]

    computed_trip_duration = computed_taxi_trip[-1]['duration']
    computed_taxi_passenger_dropoff_time = informed_taxi_pickup_time + timedelta(seconds=computed_trip_duration)

    # iterating over subway passenger routes
    for sbwy_sampn_perno_tripno, computed_sbwy_trip in dict_sbwy_trips.iteritems():

        # get informed travel data
        informed_sbwy_trip = trip_from_sampn_perno_tripno(df_trips, sbwy_sampn_perno_tripno)
        informed_sbwy_origin_time = informed_sbwy_trip['date_time_origin'].iloc[0]
        informed_sbwy_destination_time = informed_sbwy_trip['date_time_destination'].iloc[0]

        computed_sbwy_destination_time = computed_sbwy_trip[-1]['date_time']

        # verify if taxi route and subway route overlap each other temporally
        if informed_sbwy_origin_time < computed_taxi_passenger_dropoff_time\
        and informed_taxi_pickup_time < computed_sbwy_destination_time:

            # reconstruct taxi temporal routes
            computed_taxi_trip = add_date_time(informed_taxi_pickup_time, computed_taxi_trip)

            # compute overlaping of routes
            overlaped_taxi_indexes, overlaped_sbwy_indexes = time_overlaped_routes(computed_taxi_trip,\
            computed_sbwy_trip)

            overlaped_sbwy_time = computed_sbwy_trip[overlaped_sbwy_indexes[0]: overlaped_sbwy_indexes[1]]
            overlaped_taxi_time = computed_taxi_trip[overlaped_taxi_indexes[0]: overlaped_taxi_indexes[1]]

            # verify if taxi route is close to subway route
            dict_shortest_distance = integration_positions(overlaped_taxi_time, overlaped_sbwy_time)
            shortest_distance = dict_shortest_distance['shortest_distance']

            if shortest_distance < computed_taxi_trip[-1]['distance']:

                real_sbwy_intergration_index = overlaped_sbwy_indexes[0] + dict_shortest_distance['sbwy_index']
                real_taxi_intergration_index = overlaped_taxi_indexes[0] + dict_shortest_distance['taxi_index']
                sbwy_integration_pos = computed_sbwy_trip[real_sbwy_intergration_index]
                taxi_integration_pos = computed_taxi_trip[real_taxi_intergration_index]

                # compute walking distance and duration
                # for sbwy_position in range(real_sbwy_intergration_index+1):
                #     print computed_sbwy_trip[sbwy_position]

                # compute subway distance and duration


                #print 'Shareble'
                print '=>Taxi trip', taxi_sampn_perno_tripno
                print '=>Subway trip', sbwy_sampn_perno_tripno
                print 'distance', shortest_distance
                dict_match = {'taxi_trip_id': taxi_sampn_perno_tripno, 'sbwy_trip_id': sbwy_sampn_perno_tripno,\
                'stop_id': sbwy_integration_pos['stop_id'], 'integration_distance': shortest_distance,\
                'sbwy_lon': sbwy_integration_pos['longitude'], 'sbwy_lat': sbwy_integration_pos['latitude'],\
                'taxi_lon': taxi_integration_pos['longitude'], 'taxi_lat': taxi_integration_pos['latitude'],\
                'sbwy_date_time': sbwy_integration_pos['date_time'],'taxi_date_time': taxi_integration_pos['date_time']}

                list_matches.append(dict_match)
                print '============================='
                #break

    # if count_overlaped > 0:
    #     break
