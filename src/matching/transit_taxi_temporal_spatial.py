'''
    Find available taxis near transit stop that could carry transit passengers
'''
from sys import argv, path, maxint
import os
path.insert(0, os.path.abspath("../routing"))

import timeit
import pandas as pd
import numpy as np
import csv
from datetime import datetime, timedelta

from geopy.distance import great_circle
from otp_routing import OTP_routing

transit_trips_path = argv[1]
taxi_trips_path = argv[2]
max_distance = float(argv[3])
router_id = argv[4]
result_path = argv[5]
times_path = argv[6]

def format_trip_position(dict_trip):
    dict_formated_trip = dict_trip
    dict_formated_trip['trip_sequence'] = int(dict_trip['trip_sequence'])
    dict_formated_trip['pos_sequence'] = int(dict_trip['pos_sequence'])
    dict_formated_trip['date_time'] = datetime.strptime(dict_trip['date_time'], '%Y-%m-%d %H:%M:%S.%f')
    dict_formated_trip['longitude'] = float(dict_trip['longitude'])
    dict_formated_trip['latitude'] =  float(dict_trip['latitude'])
    if len(dict_trip['distance']) > 0:
        dict_formated_trip['distance'] = float(dict_trip['distance'])
    else:
        dict_formated_trip['distance'] = 0.0
    return dict_formated_trip

def generate_trip(trips_path, list_modes):
    with open(trips_path, 'rb') as in_file:
        csv_reader = csv.reader(in_file, delimiter=',')
        csv_headings = next(csv_reader)
        list_trip = []
        try:
            previous_pos = dict(zip(csv_headings, next(csv_reader)))
            if previous_pos['mode'] in list_modes:
                list_trip.append(format_position(previous_pos))

            while True:
                current_pos = dict(zip(csv_headings, next(csv_reader)))
                if current_pos['mode'] in list_modes:
                    if len(list_trip) == 0 or (len(list_trip) > 0 and list_trip[-1]['sampn_perno_tripno'] == current_pos['sampn_perno_tripno']):
                        list_trip.append(format_trip_position(current_pos))
                    elif list_trip[-1]['sampn_perno_tripno'] != current_pos['sampn_perno_tripno']:
                        yield list_trip
                        list_trip = []
                        list_trip.append(format_trip_position(current_pos))

        except csv.Error:
            print "Error"
        except StopIteration:
            print "Iteration End"
            yield list_trip

def read_trips(trips_path, list_modes):
    dict_trips = dict()

    with open(trips_path, 'rb') as in_file:
        csv_reader = csv.reader(in_file, delimiter=',')
        csv_headings = next(csv_reader)

        for current_pos in csv_reader:
            dict_pos = dict(zip(csv_headings, current_pos))
            if dict_pos['mode'] in list_modes:
                dict_trips.setdefault(dict_pos['sampn_perno_tripno'], []).append(format_trip_position(dict_pos))

    return dict_trips

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

# def read_transit_trips(transit_trips_path):
#     dict_transit_trips = dict()
#
#     df_transit_trips = pd.read_csv(transit_trips_path)
#     # df_transit_trips = df_transit_trips.head(10000)
#     df_transit_trips = df_transit_trips[(df_transit_trips['mode'] == 'WALK')\
#     | (df_transit_trips['mode'] == 'BUS') | (df_transit_trips['mode'] == 'SUBWAY')]
#     df_transit_trips['date_time'] = pd.to_datetime(df_transit_trips['date_time'])
#     dict_transit_trips = group_df_rows(df_transit_trips, 'sampn_perno_tripno')
#     del df_transit_trips
#
#     return dict_transit_trips


# def read_taxi_trips(taxi_trips_path):
#     dict_taxi_trips = dict()
#
#     df_taxi_trips = pd.read_csv(taxi_trips_path)
#     df_taxi_trips = df_taxi_trips[df_taxi_trips['mode'] == 'TAXI']
#     df_taxi_trips['date_time'] = pd.to_datetime(df_taxi_trips['date_time'])
#     dict_taxi_trips = group_df_rows(df_taxi_trips, 'sampn_perno_tripno')
#     del df_taxi_trips
#
#     return dict_taxi_trips

# def running_taxis_near_stop(transit_stop_position, dict_taxi_trips, max_distance):
#     # get running taxis
#
#     # find those are near bus stop
#     return list_taxis_near_stop

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

def otp_route_positions(router_id, lat_origin, lon_origin, lat_destination, lon_destination, mode, date_time):
    otp = OTP_routing(router_id)

    # origin and destination lie on the same census tract
    if lat_origin == lat_destination and lon_origin == lon_destination:
        return [{'date_time': date_time, 'distance': 0.0, 'longitude': lon_origin, 'mode': mode,\
        'trip_sequence': 1, 'stop_id': '', 'latitude': lat_origin, 'pos_sequence': 1}]

    route_positions = otp.route_positions(lat_origin, lon_origin, lat_destination, lon_destination, mode, date_time)
    return route_positions

def integration_route(router_id, transit_stop_position, taxi_acceptance_position, transit_destination_position,\
taxi_destination_position, integration_transit_destination_trip):

    # integration_taxi -> integration_transit
    integration_taxi_trip = otp_route_positions(router_id, taxi_acceptance_position['latitude'],\
    taxi_acceptance_position['longitude'], transit_stop_position['latitude'], transit_stop_position['longitude'],\
    'CAR', taxi_acceptance_position['date_time'])
    if len(integration_taxi_trip) == 0:
        return {}, list()

    integration_distance = float(integration_taxi_trip[-1]['distance'])
    taxi_arrival_time_transit_stop = integration_taxi_trip[-1]['date_time']
    transit_arrival_time_stop = transit_stop_position['date_time']

    # find who would arrive at the integration stop first
    taxi_departure_time_transit_stop = taxi_arrival_time_transit_stop
    if transit_arrival_time_stop > taxi_arrival_time_transit_stop:
        taxi_departure_time_transit_stop = transit_arrival_time_stop

    # the integration could not begin after the expected arrival time at the taxi passenger destination
    if transit_destination_position['date_time'] < taxi_destination_position['date_time']:

        # find which destination comes first
        distance_integration_transit_destination = great_circle((transit_stop_position['latitude'], transit_stop_position['longitude']),\
        (transit_destination_position['latitude'], transit_destination_position['longitude']))
        distance_integration_taxi_destination = great_circle((transit_stop_position['latitude'], transit_stop_position['longitude']),\
        (taxi_destination_position['latitude'], taxi_destination_position['longitude']))

        # taxi destination comes first
        if distance_integration_taxi_destination < distance_integration_transit_destination:
            # compute the route from integration to taxi destination
            integration_taxi_destination_trip = otp_route_positions(router_id,transit_stop_position['latitude'],\
            transit_stop_position['longitude'], taxi_destination_position['latitude'], taxi_destination_position['longitude'],\
            'CAR', taxi_departure_time_transit_stop)

            if len(integration_taxi_destination_trip) == 0:
                return {}, list()
            integration_taxi_destination_time = integration_taxi_destination_trip[-1]['date_time']

            # compute the route from taxi destination to transit destination
            destination_taxi_destination_transit_trip = otp_route_positions(router_id, taxi_destination_position['latitude'],\
            taxi_destination_position['longitude'], transit_destination_position['latitude'],\
            transit_destination_position['longitude'], 'CAR', integration_taxi_destination_time)
            if len(destination_taxi_destination_transit_trip) == 0:
                return {}, list()
            integration_transit_destination_time = destination_taxi_destination_transit_trip[-1]['date_time']

            shared_distance = float(integration_taxi_destination_trip[-1]['distance'])
            destinations_distance = float(destination_taxi_destination_transit_trip[-1]['distance'])

        # transit destination comes first
        else:
            # compute the route from integration to transit destination
            # if it is not in cache
            if len(integration_transit_destination_trip) == 0:
                integration_transit_destination_trip = otp_route_positions(router_id, transit_stop_position['latitude'],\
                transit_stop_position['longitude'], transit_destination_position['latitude'], transit_destination_position['longitude'],\
                'CAR', taxi_departure_time_transit_stop)

                if len(integration_transit_destination_trip) == 0:
                    return {}, list()

            integration_transit_destination_time = integration_transit_destination_trip[-1]['date_time']

            # compute the route from transit destination to taxi destination
            destination_transit_destination_taxi_trip = otp_route_positions(router_id, transit_destination_position['latitude'],\
            transit_destination_position['longitude'], taxi_destination_position['latitude'],\
            taxi_destination_position['longitude'],  'CAR', integration_transit_destination_time)
            if len(destination_transit_destination_taxi_trip) == 0:
                return {}, list()
            integration_taxi_destination_time = destination_transit_destination_taxi_trip[-1]['date_time']

            shared_distance = float(integration_transit_destination_trip[-1]['distance'])
            destinations_distance = float(destination_transit_destination_taxi_trip[-1]['distance'])

        # transit passenger save time with the shared route
        if integration_transit_destination_time < transit_destination_position['date_time']:

            return {'taxi_destination_time': integration_taxi_destination_time,\
            'transit_destination_time': integration_transit_destination_time,\
            'taxi_arrival_time_transit_stop': taxi_arrival_time_transit_stop, 'integration_distance': integration_distance,\
            'shared_distance': shared_distance, 'destinations_distance': destinations_distance},\
            integration_transit_destination_trip

    return {}, list()

def match_transit_taxi_trips(router_id, list_transit_trip, dict_taxi_trips, max_distance):
    list_transit_taxi_matches = []
    list_time_per_transit_id = []
    # transit_id = (list_transit_trip['id'])
    # for transit_id, list_transit_trip in dict_transit_trips.iteritems():

    start_time = timeit.default_timer()
    # print 'transit_id', transit_id

    # integrations happens on the stop station
    list_stops = [position for position in list_transit_trip if type(position['stop_id']) != float]

    # for each transit stop
    dict_stops_available_taxis = dict()
    for transit_stop_position in list_stops:

        # cache to prevent extra computation
        integration_transit_destination_trip = list()

        # find running taxis until x meters from the stop
        print 'find matches'
        dict_running_taxis = running_taxi_trips(transit_stop_position['date_time'], dict_taxi_trips)
        list_taxis_near_stop = taxis_near_stop(transit_stop_position, dict_running_taxis, max_distance)

        if len(list_taxis_near_stop) > 0:
            # print transit_stop_position
            for taxi_near_stop in list_taxis_near_stop:
                # print taxi_near_stop['taxi_id']

                list_taxi_positions = dict_taxi_trips[taxi_near_stop['taxi_id']]
                taxi_acceptance_position = [position for position in list_taxi_positions\
                if position['pos_sequence'] == taxi_near_stop['pos_sequence']][0]

                transit_destination_position = list_transit_trip[-1]
                taxi_destination_position = list_taxi_positions[-1]

                dict_match_times_distances, integration_transit_destination_trip = integration_route(router_id,\
                transit_stop_position, taxi_acceptance_position, transit_destination_position,\
                taxi_destination_position, integration_transit_destination_trip)

                if len(dict_match_times_distances) > 0:

                    # dict_match_times_distances['transit_id'] = transit_id
                    dict_match_times_distances['stop_id'] = transit_stop_position['stop_id']

                    dict_match_times_distances['taxi_id'] = taxi_near_stop['taxi_id']
                    dict_match_times_distances['taxi_pos_sequence'] = taxi_near_stop['pos_sequence']

                    list_transit_taxi_matches.append(dict_match_times_distances)
                    # print transit_stop_position['stop_id'], taxi_near_stop['taxi_id']
        elapsed = timeit.default_timer() - start_time
        # list_time_per_transit_id.append({'transit_id': transit_id, 'elapsed': elapsed})
    return list_transit_taxi_matches, list_time_per_transit_id

# print 'reading transit data...'
# dict_transit_trips = read_transit_trips(transit_trips_path)
print 'reading taxi data...'
dict_taxi_trips = read_trips(taxi_trips_path, ['TAXI'])
# df_taxi_trips = read_taxi_trips(taxi_trips_path)

# print 'transit_trips', len(dict_transit_trips)
print 'taxi_trips', len(dict_taxi_trips)

start_time = timeit.default_timer()

list_transit_taxi_matches = []
list_time_per_transit_id = []
count = 0
for list_transit_trip in generate_trip(transit_trips_path, ['BUS', 'SUBWAY']):
    # print list_transit_trip
    list_transit_taxi_matches, list_time_per_transit_id = match_transit_taxi_trips(router_id,\
    list_transit_trip, dict_taxi_trips, max_distance)
    print count
    count += 1
elapsed = timeit.default_timer() - start_time
print 'matching_time', elapsed

df_transit_taxi_matches = pd.DataFrame(list_transit_taxi_matches)
df_time_per_transit_id = pd.DataFrame(list_time_per_transit_id)

df_transit_taxi_matches = df_transit_taxi_matches[['transit_id', 'stop_id', 'taxi_id', 'taxi_pos_sequence',\
'taxi_arrival_time_transit_stop', 'taxi_destination_time', 'transit_destination_time', 'integration_distance',\
'shared_distance', 'destinations_distance']]

print df_transit_taxi_matches
print 'matches', len(list_transit_taxi_matches)

df_transit_taxi_matches.to_csv(result_path, index = False)
df_time_per_transit_id.to_csv(times_path, index = False)
