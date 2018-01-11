'''
    Find matches from transit and taxi trips considering temporal, spatial and cost constraints
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
router_id = argv[3]
max_distance = float(argv[4])
transit_initial_cost_parcel = float(argv[5])
transit_integration_cost_parcel = float(argv[6])
transit_shared_cost_parcel = float(argv[7])
result_path = argv[8]

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())

    # for key, list_dict in dict_grouped.iteritems():
    #     dict_grouped[key] = sorted(list_dict, key=lambda pos: (pos['trip_sequence'], pos['pos_sequence']))
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

def read_taxi_trips(taxi_trips_path):
    dict_taxi_trips = dict()

    df_taxi_trips = pd.read_csv(taxi_trips_path)
    df_taxi_trips = df_taxi_trips[df_taxi_trips['mode'] == 'TAXI']
    df_taxi_trips['date_time'] = pd.to_datetime(df_taxi_trips['date_time'])
    dict_taxi_trips = group_df_rows(df_taxi_trips, 'sampn_perno_tripno')
    del df_taxi_trips

    return dict_taxi_trips

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

def match_transit_taxi_trips(dict_transit_trips, dict_taxi_trips, max_distance):
    list_transit_taxi_matches = []
    for transit_id, list_transit_trip in dict_transit_trips.iteritems():
        # print 'transit_id', transit_id

        # integrations happens on the stop station
        list_stops = [position for position in list_transit_trip if type(position['stop_id']) != float]

        # for each transit stop
        dict_stops_available_taxis = dict()
        for transit_stop_position in list_stops:

            # cache to prevent extra computation
            integration_transit_destination_trip = list()

            # find running taxis until x meters from the stop
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

                        dict_match_times_distances['transit_id'] = transit_id
                        dict_match_times_distances['stop_id'] = transit_stop_position['stop_id']

                        dict_match_times_distances['taxi_id'] = taxi_near_stop['taxi_id']
                        dict_match_times_distances['taxi_pos_sequence'] = taxi_near_stop['pos_sequence']

                        list_transit_taxi_matches.append(dict_match_times_distances)
                        # print transit_stop_position['stop_id'], taxi_near_stop['taxi_id']

    return pd.DataFrame(list_transit_taxi_matches)

def nyc_taxi_cost(date_time_origin, trip_distance_meters, stopped_duration_sec):

    # costs in dolar
    initial_charge = 2.5
    tax_per_ride = 0.5
    rate_per_mile = 2.5 # 50 cents per 1/5 mile
    rate_per_minute_stopped = 0.4 # per minute
    peak_hour_surcharge = 1 # Mon - Fri 4pm to 8pm
    night_surcharge = 0.5 # 8pm to 6am

    peak_weekdays = range(0, 5) # Mon - Fri
    peak_hours = range(16, 20) # 4pm to 8pm
    night_hours = range(20, 24) + range(0,7) # 8pm to 6am

    mile_in_meters = 0.000621371

    # airport
    # surcharge_to_newark = 15
    # jfk_manhattan = 45

    ride_cost = initial_charge + tax_per_ride
    # peak hours
    if date_time_origin.weekday() in peak_weekdays and date_time_origin.hour in peak_hours:
        ride_cost += peak_hour_surcharge

    # night
    if date_time_origin.hour in night_hours:
        ride_cost += night_surcharge

    # distance
    price_per_meter = mile_in_meters * rate_per_mile
    ride_cost += price_per_meter * trip_distance_meters

    # stopped duration
    ride_cost += (stopped_duration_sec/60) * rate_per_minute_stopped

    return ride_cost

def nyc_transit_taxi_shared_costs(transit_initial_cost_parcel, transit_integration_cost_parcel,\
transit_shared_cost_parcel, date_time_origin, origin_distance, origin_stopped_time,\
integration_distance, integration_stopped_time, shared_distance, shared_stopped_time,\
transit_destination_first, destinations_distance, destinations_stopped_time):

    # costs in dolar
    initial_charge = 2.5
    tax_per_ride = 0.5
    rate_per_mile = 2.5 # 50 cents per 1/5 mile
    rate_per_minute_stopped = 0.4 # per minute
    peak_hour_surcharge = 1 # Mon - Fri 4pm to 8pm
    night_surcharge = 0.5 # 8pm to 6am

    peak_weekdays = range(0, 5) # Mon - Fri
    peak_hours = range(16, 20) # 4pm to 8pm
    night_hours = range(20, 24) + range(0,7) # 8pm to 6am

    mile_in_meters = 0.000621371

    taxi_passenger_cost = 0
    transit_passenger_cost = 0

    initial_cost = initial_charge + tax_per_ride

    # peak hours
    if date_time_origin.weekday() in peak_weekdays and date_time_origin.hour in peak_hours:
        initial_cost += peak_hour_surcharge

    # night
    if date_time_origin.hour in night_hours:
        initial_cost += night_surcharge

    transit_passenger_cost = initial_cost * transit_initial_cost_parcel
    taxi_passenger_cost = initial_cost * (1 - transit_initial_cost_parcel)


    price_per_meter = mile_in_meters * rate_per_mile

    # origin-acceptance
    taxi_passenger_cost += origin_distance * price_per_meter
    taxi_passenger_cost += ((origin_stopped_time/60) * rate_per_minute_stopped)

    # acceptance-integration
    distance_integration_cost = integration_distance * price_per_meter
    stopped_integration_cost = ((integration_stopped_time/60) * rate_per_minute_stopped)
    total_integration_cost = distance_integration_cost + stopped_integration_cost

    transit_passenger_cost += total_integration_cost * transit_initial_cost_parcel
    taxi_passenger_cost += total_integration_cost * (1 - transit_initial_cost_parcel)

    # integration-first_destination
    distance_shared_cost = (shared_distance * price_per_meter)
    stopped_shared_cost = (((shared_stopped_time)/60) * rate_per_minute_stopped)
    total_shared_cost = distance_shared_cost + stopped_shared_cost

    transit_passenger_cost += total_shared_cost * transit_shared_cost_parcel
    taxi_passenger_cost += total_shared_cost * (1 - transit_shared_cost_parcel)

    # first_destination-last_destination
    if transit_destination_first == True:
        taxi_passenger_cost += destinations_distance * price_per_meter
        taxi_passenger_cost += (destinations_stopped_time/60) * rate_per_minute_stopped
    else:
        transit_passenger_cost += destinations_distance * price_per_meter
        transit_passenger_cost += (destinations_stopped_time/60) * rate_per_minute_stopped

    return transit_passenger_cost, taxi_passenger_cost

def compute_integration_costs(transit_initial_cost_parcel, transit_integration_cost_parcel,\
transit_shared_cost_parcel, dict_transit_private_trip, dict_taxi_private_trip, df_matches):

    list_integration_costs = []

    for index, matching in df_matches.iterrows():

        list_transit_trip = dict_transit_private_trip[matching['transit_id']]
        list_taxi_private_trip = dict_taxi_private_trip[matching['taxi_id']]

        taxi_private_cost = nyc_taxi_cost(list_taxi_private_trip[0]['date_time'], list_taxi_private_trip[-1]['distance'], 0)

        taxi_acceptance_position = [position for position in list_taxi_private_trip\
        if position['pos_sequence'] == matching['taxi_pos_sequence']][0]

        transit_stop_position = [position for position in list_transit_trip\
        if position['stop_id'] == matching['stop_id']][0]

        integration_stopped_time = 0
        if transit_stop_position['date_time'] > matching['taxi_arrival_time_transit_stop']:
            integration_stopped_time = (transit_stop_position['date_time'] - matching['taxi_arrival_time_transit_stop']).total_seconds()

        transit_destination_first = False
        if matching['transit_destination_time'] < matching['taxi_destination_time']:
            transit_destination_first = True

        transit_shared_cost, taxi_shared_cost = nyc_transit_taxi_shared_costs(transit_initial_cost_parcel,\
        transit_integration_cost_parcel, transit_shared_cost_parcel,\
        list_taxi_private_trip[0]['date_time'], taxi_acceptance_position['distance'], 0,\
        matching['integration_distance'], integration_stopped_time,\
        matching['shared_distance'], 0,\
        transit_destination_first, matching['destinations_distance'], 0)

        # taxi passenger save time
        if taxi_shared_cost < taxi_private_cost:
            list_integration_costs.append({'match_index': index, 'taxi_private_cost': taxi_private_cost,\
            'taxi_shared_cost': taxi_shared_cost, 'transit_shared_cost': transit_shared_cost})

    return pd.DataFrame(list_integration_costs)

def merge_matches(df_temporal_spatial_match, df_cost_match):
    list_matches = []
    for index, costs in df_cost_match.iterrows():
        dict_match = df_temporal_spatial_match.loc[int(costs['match_index'])].to_dict()
        dict_match['taxi_private_cost'] = costs['taxi_private_cost']
        dict_match['taxi_shared_cost'] = costs['taxi_shared_cost']
        dict_match['transit_shared_cost'] = costs['transit_shared_cost']
        list_matches.append(dict_match)

    return pd.DataFrame(list_matches)

def best_integration_possibility(df_matches, df_transit_private_trip):
    dict_transit_taxis = group_df_rows(df_matches, 'transit_id')
    dict_best_possibilities = dict()
    for transit_id, list_possibilities in dict_transit_taxis.iteritems():
        # print transit_id, len(list_possibilities)
        maximum_utility = -maxint
        best_stop_integration = ''
        for possibility in list_possibilities:
            df_original_transit = df_transit_private_trip[(df_transit_private_trip['sampn_perno_tripno'] == transit_id)]
            original_destination_time = df_original_transit['date_time'].iloc[-1]
            transit_saving_time = (original_destination_time - possibility['transit_destination_time']).total_seconds()
            taxi_saving_money = possibility['taxi_private_cost'] - possibility['taxi_shared_cost']

            # combine utilities
            integration_utility = transit_saving_time * taxi_saving_money

            # get the maximum utility
            if integration_utility > maximum_utility:
                maximum_utility = integration_utility
                possibility['transit_original_destination_time'] = original_destination_time
                dict_best_possibilities[transit_id] = possibility

    return dict_best_possibilities

# read transit trips
df_transit_trips = pd.read_csv(transit_trips_path)
# df_transit_trips = df_transit_trips.head(10000)
df_transit_trips = df_transit_trips[(df_transit_trips['mode'] == 'WALK')\
| (df_transit_trips['mode'] == 'BUS') | (df_transit_trips['mode'] == 'SUBWAY')]
df_transit_trips['date_time'] = pd.to_datetime(df_transit_trips['date_time'])
dict_transit_trips = group_df_rows(df_transit_trips, 'sampn_perno_tripno')

# read_taxi_trips
df_taxi_trips = pd.read_csv(taxi_trips_path)
df_taxi_trips = df_taxi_trips[df_taxi_trips['mode'] == 'TAXI']
df_taxi_trips['date_time'] = pd.to_datetime(df_taxi_trips['date_time'])
dict_taxi_trips = group_df_rows(df_taxi_trips, 'sampn_perno_tripno')

print 'transit_trips', len(dict_transit_trips)
print 'taxi_trips', len(dict_taxi_trips)

df_temporal_spatial_match = match_transit_taxi_trips(dict_transit_trips, dict_taxi_trips, max_distance)
df_cost_match = compute_integration_costs(transit_initial_cost_parcel, transit_integration_cost_parcel,\
transit_shared_cost_parcel, dict_transit_trips, dict_taxi_trips, df_temporal_spatial_match)
df_matches = merge_matches(df_temporal_spatial_match, df_cost_match)

dict_best_possibilities = best_integration_possibility(df_matches, df_transit_trips)

list_best_integration = []
for transit_id, dict_integration in dict_best_possibilities.iteritems():
    # print transit_id, dict_integration
    dict_integration['transit_id'] = transit_id
    list_best_integration.append(dict_integration)

df_best_integration = pd.DataFrame(list_best_integration)
print df_best_integration
df_best_integration = df_best_integration[['transit_id', 'stop_id', 'taxi_id', 'taxi_pos_sequence',\
'taxi_arrival_time_transit_stop', 'taxi_destination_time', 'transit_destination_time',\
'transit_original_destination_time','integration_distance', 'shared_distance', 'destinations_distance',\
'taxi_private_cost', 'taxi_shared_cost', 'transit_shared_cost']]
print df_best_integration

df_best_integration.to_csv(result_path, index=False)
