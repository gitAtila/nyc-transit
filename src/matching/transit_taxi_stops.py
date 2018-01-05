'''
    Find available taxis near transit stop
'''
from sys import argv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

transit_trips_path = argv[1]
taxi_trips_path = argv[2]
distance = argv[3]
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

def running_taxi_near_stops(list_transit_trip, dict_taxi_trips, distance):
    # for each transit stop
    list_stops = [position for position in list_transit_trip if type(position['stop_id']) != float]
    for stop in list_stops:
        print stop['date_time']
        break
        # find running taxis x meters from the stop

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

for sampn_perno_tripno, list_transit_trip in dict_transit_trips.iteritems():
    running_taxi_near_stops(list_transit_trip, dict_taxi_trips, distance)
    break
