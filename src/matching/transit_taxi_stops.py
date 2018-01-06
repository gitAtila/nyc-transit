'''
    Find available taxis near transit stop
'''
from sys import argv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from geopy.distance import great_circle

transit_trips_path = argv[1]
taxi_trips_path = argv[2]
max_distance = argv[3]
result_path = argv[4]

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())

    for key, list_dict in dict_grouped.iteritems():
        dict_grouped[key] = sorted(list_dict, key=lambda pos: (pos['trip_sequence'], pos['pos_sequence']))
    return dict_grouped

def trips_by_modes(df_trips, list_modes):
    df_trips = df_trips[df_trips['mode'].isin(list_modes)]
    # print df_trips
    dict_trips = group_df_rows(df_trips, 'sampn_perno_tripno')

    dict_valid_trips = dict()
    for key, list_positions in dict_trips.iteritems():
        is_valid = True
        for dict_position in list_positions:
            if dict_position['mode'] not in list_modes:
                is_valid = False
                break
        if is_valid == True:
            dict_valid_trips[key] = list_positions
    return dict_valid_trips

def running_taxi_trips(date_time, dict_taxi_trips):
    dict_running_taxis = dict()
    for key, list_taxi_positions in dict_taxi_trips.iteritems():
        if list_taxi_positions[0]['date_time'] < date_time and list_taxi_positions[-1]['date_time'] > date_time:
            dict_running_taxis[key] = list_taxi_positions
    return dict_running_taxis

def taxis_near_stop(stop, dict_running_taxis, max_distance):
    list_taxis_near_stop = []

    for key, list_taxi_positions in dict_running_taxis.iteritems():
        for taxi_position in list_taxi_positions:
            distance_stop_taxi_pos = great_circle((stop['latitude'], stop['longitude']),\
            (taxi_position['latitude'], taxi_position['longitude'])).meters
            if distance_stop_taxi_pos <= max_distance:
                list_taxis_near_stop.append({'taxi_id': key, 'trip_sequence': taxi_position['trip_sequence'],\
                'pos_sequence': taxi_position['pos_sequence'], 'distance': distance_stop_taxi_pos})

    return list_taxis_near_stop

def match_transit_taxi_trips(dict_transit_trips, dict_taxi_trips, max_distance):
    dict_transit_taxi_matches = dict()
    for sampn_perno_tripno, list_transit_trip in dict_transit_trips.iteritems():

        # integrations happens on the stop station
        list_stops = [position for position in list_transit_trip if type(position['stop_id']) != float]
        # for each transit stop
        dict_stops_available_taxis = dict()
        for stop in list_stops:

            # find running taxis until x meters from the stop
            dict_running_taxis = running_taxi_trips(stop['date_time'], dict_taxi_trips)
            list_taxis_near_stop = taxis_near_stop(stop, dict_running_taxis, max_distance)
            if len(list_taxis_near_stop) > 0:
                dict_stops_available_taxis[stop['stop_id']] = list_taxis_near_stop

        if len(dict_stops_available_taxis) > 0:
            print '\n', sampn_perno_tripno, len(dict_stops_available_taxis) 
            dict_transit_taxi_matches[sampn_perno_tripno] = dict_stops_available_taxis

    return dict_transit_taxi_matches

# read transit trips
df_transit_trips = pd.read_csv(transit_trips_path)
df_transit_trips = df_transit_trips.head(1000)
df_transit_trips = df_transit_trips[(df_transit_trips['mode'] == 'WALK')\
| (df_transit_trips['mode'] == 'BUS') | (df_transit_trips['mode'] == 'SUBWAY')]
df_transit_trips['date_time'] = pd.to_datetime(df_transit_trips['date_time'])
dict_transit_trips = group_df_rows(df_transit_trips, 'sampn_perno_tripno')
del df_transit_trips
print 'transit_trips', len(dict_transit_trips)

# read taxi trips
df_taxi_trips = pd.read_csv(taxi_trips_path)
df_taxi_trips = df_taxi_trips[df_taxi_trips['mode'] == 'TAXI']
df_taxi_trips['date_time'] = pd.to_datetime(df_taxi_trips['date_time'])
dict_taxi_trips = group_df_rows(df_taxi_trips, 'sampn_perno_tripno')
del df_taxi_trips
print 'taxi_trips', len(dict_taxi_trips)

dict_transit_taxi_matches = match_transit_taxi_trips(dict_transit_trips, dict_taxi_trips, max_distance)
print len(dict_transit_taxi_matches)
