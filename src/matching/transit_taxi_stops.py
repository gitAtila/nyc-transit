'''
    Find available taxis near transit stop
'''
from sys import argv, path, maxint
import os
path.insert(0, os.path.abspath("../routing"))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from geopy.distance import great_circle
from otp_routing import OTP_routing

transit_trips_path = argv[1]
taxi_trips_path = argv[2]
max_distance = float(argv[3])
router_id = argv[4]
result_path = argv[5]

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

def integration_route(transit_stop_position, taxi_acceptance_position, transit_destination_position, taxi_destination_position):
    otp = OTP_routing(router_id)

    # integration_taxi -> integration_transit
    integration_taxi_trip = otp.route_positions(taxi_acceptance_position['latitude'], taxi_acceptance_position['longitude'],\
    transit_stop_position['latitude'], transit_stop_position['longitude'], 'CAR', taxi_acceptance_position['date_time'])
    if len(integration_taxi_trip) == 0:
        return {}

    integration_distance = float(integration_taxi_trip[-1]['distance'])

    taxi_arrival_time_transit_stop = integration_taxi_trip[-1]['date_time']
    transit_arrival_time_stop = transit_stop_position['date_time']

    taxi_passenger_destination_time = taxi_destination_position['date_time']
    transit_passenger_destination_time = transit_destination_position['date_time']

    # find who would arrive at the integration stop first
    taxi_departure_time_transit_stop = taxi_arrival_time_transit_stop
    if transit_arrival_time_stop > taxi_arrival_time_transit_stop:
        taxi_departure_time_transit_stop = transit_arrival_time_stop

    # the integration could not begin after the destination time of taxi passenger
    if taxi_departure_time_transit_stop < taxi_passenger_destination_time:

        # integration_transit -> destination_transit
        integration_transit_destination_trip = otp.route_positions(transit_stop_position['latitude'], transit_stop_position['longitude'],\
        transit_destination_position['latitude'], transit_destination_position['longitude'], 'CAR', taxi_departure_time_transit_stop)
        if len(integration_transit_destination_trip) == 0:
            return {}
        integration_transit_destination_time = integration_transit_destination_trip[-1]['date_time']

        # integration_transit -> destination_taxi
        integration_taxi_destination_trip = otp.route_positions(transit_stop_position['latitude'], transit_stop_position['longitude'],\
        taxi_destination_position['latitude'], taxi_destination_position['longitude'], 'CAR', taxi_departure_time_transit_stop)
        if len(integration_taxi_destination_trip) == 0:
            return {}
        integration_taxi_destination_time = integration_taxi_destination_trip[-1]['date_time']

        if integration_taxi_destination_time < integration_transit_destination_time:

            # destination_taxi -> destination_transit
            destination_taxi_destination_transit_trip = otp.route_positions(integration_taxi_destination_trip[-1]['latitude'],\
            integration_taxi_destination_trip[-1]['longitude'], integration_transit_destination_trip[-1]['latitude'],\
            integration_transit_destination_trip[-1]['longitude'], 'CAR', integration_taxi_destination_time)
            if len(destination_taxi_destination_transit_trip) == 0:
                return {}
            integration_transit_destination_time = destination_taxi_destination_transit_trip[-1]['date_time']

            shared_distance = float(integration_taxi_destination_trip[-1]['distance'])
            destinations_distance = float(destination_taxi_destination_transit_trip[-1]['distance'])

        else:
            # destination_transit -> destination_taxi
            destination_transit_destination_taxi_trip = otp.route_positions(integration_transit_destination_trip[-1]['latitude'],\
            integration_transit_destination_trip[-1]['longitude'], integration_taxi_destination_trip[-1]['latitude'],\
            integration_taxi_destination_trip[-1]['longitude'],  'CAR', integration_transit_destination_time)
            if len(destination_transit_destination_taxi_trip) == 0:
                return {}
            integration_taxi_destination_time = destination_transit_destination_taxi_trip[-1]['date_time']

            shared_distance = float(integration_transit_destination_trip[-1]['distance'])
            destinations_distance = float(destination_transit_destination_taxi_trip[-1]['distance'])

        # transit passenger save time with the shared route
        if integration_transit_destination_time < transit_passenger_destination_time:

            return {'taxi_destination_time': integration_taxi_destination_time,\
            'transit_destination_time': integration_transit_destination_time,\
            'taxi_arrival_time_transit_stop': taxi_arrival_time_transit_stop, 'integration_distance': integration_distance,\
            'shared_distance': shared_distance, 'destinations_distance': destinations_distance}

    return {}

def match_transit_taxi_trips(dict_transit_trips, dict_taxi_trips, max_distance):
    dict_transit_taxi_matches = dict()
    for sampn_perno_tripno, list_transit_trip in dict_transit_trips.iteritems():

        # integrations happens on the stop station
        list_stops = [position for position in list_transit_trip if type(position['stop_id']) != float]
        # for each transit stop
        dict_stops_available_taxis = dict()
        for transit_stop_position in list_stops:

            # find running taxis until x meters from the stop
            dict_running_taxis = running_taxi_trips(transit_stop_position['date_time'], dict_taxi_trips)
            list_taxis_near_stop = taxis_near_stop(transit_stop_position, dict_running_taxis, max_distance)

            if len(list_taxis_near_stop) > 0:
                # print transit_stop_position
                for taxi_near_stop in list_taxis_near_stop:
                    # print taxi_near_stop
                    list_taxi_positions = dict_taxi_trips[taxi_near_stop['taxi_id']]
                    taxi_acceptance_position = [position for position in list_taxi_positions\
                    if position['pos_sequence'] == taxi_near_stop['pos_sequence']][0]
                    # print taxi_acceptance_position
                    transit_destination_position = list_transit_trip[-1]
                    taxi_destination_position = list_taxi_positions[-1]
                    
                    dict_match_times_distances = integration_route(transit_stop_position, taxi_acceptance_position,\
                    transit_destination_position, taxi_destination_position)

                    print dict_match_times_distances
                    # dict_stops_available_taxis[transit_stop_position['stop_id']] = list_taxis_near_stop

        # if len(dict_stops_available_taxis) > 0:
        #     # print '\n', sampn_perno_tripno, len(dict_stops_available_taxis)
        #     dict_transit_taxi_matches[sampn_perno_tripno] = dict_stops_available_taxis

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
# for transit_id, dict_stop_taxis in dict_transit_taxi_matches.iteritems():
#     print transit_id, dict_stop_taxis.keys()
print 'matches', len(dict_transit_taxi_matches)

# compute elegible taxi
