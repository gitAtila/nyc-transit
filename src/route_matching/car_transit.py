'''
    Match car and transit passenger trips
'''
from sys import argv, path, maxint
import os
path.insert(0, os.path.abspath("../map_routing"))

import pandas as pd
import math
from datetime import datetime, timedelta

from otp_routing import OTP_routing

survey_trips_path = argv[1]
transit_trips_path = argv[2]
transit_mode_codes = argv[3]
car_trips_path = argv[4]
car_mode_codes = argv[5]
router_id = argv[6]
result_path = argv[7]

# reconstruct passenger_route
def reconstruct_passenger_route(df_transit_passenger_trips, df_stop_times):
    list_passenger_trip_id = set(df_transit_passenger_trips['sampn_perno_tripno'].tolist())
    dict_passenger_routes = dict()

    for passenger_trip_id in list_passenger_trip_id:
        # trips of the same travel
        df_transit_passenger_route = df_transit_passenger_trips[df_transit_passenger_trips['sampn_perno_tripno'] == passenger_trip_id]
        df_transit_passenger_route = df_transit_passenger_route.sort_values('trip_sequence')

        list_passenger_trips = []
        for index, passenger_trip in df_transit_passenger_route.iterrows():
            # select timestable of transit trip
            df_transit_trip = df_stop_times[df_stop_times['trip_id'] == passenger_trip['gtfs_trip_id']]
            # select times and stops of passenger boading until alight
            boarding_stop = df_transit_trip[df_transit_trip['stop_id'] == passenger_trip['boarding_stop_id']]
            alighting_stop = df_transit_trip[df_transit_trip['stop_id'] == passenger_trip['alighting_stop_id']]
            boarding_index = int(boarding_stop.index[0])
            alighting_index = int(alighting_stop.index[0])
            df_transit_trip = df_transit_trip.loc[boarding_index: alighting_index]
            # convert stop times in a list of dictionaries
            list_passenger_trip = df_transit_trip[['departure_time', 'stop_id', 'stop_sequence']].T.to_dict().values()
            list_passenger_trips.append(sorted(list_passenger_trip, key=lambda stop: stop['stop_sequence']))

        dict_passenger_routes[passenger_trip_id] = list_passenger_trips

    return dict_passenger_routes

def trip_from_sampn_perno_tripno(df_trips, sampn_perno_tripno):
    sampn_perno_tripno = sampn_perno_tripno.split('_')
    informed_trip = df_trips[(df_trips['sampn'] == int(sampn_perno_tripno[0]))\
     & (df_trips['perno'] == int(sampn_perno_tripno[1]))\
     & (df_trips['tripno'] == int(sampn_perno_tripno[2]))]
    return informed_trip


def time_overlaped_routes(list_car_route, computed_transit_trip):

    car_first_index = 0
    transit_first_index = 0

    # car starts first
    if list_car_route[0]['date_time'] < computed_transit_trip[0]['date_time']:
        for index in range(1, len(list_car_route)):
            if list_car_route[index]['date_time'] >= computed_transit_trip[0]['date_time']:
                car_frist_index = index
                break
    else: # transit starts first
        for index in range(1, len(computed_transit_trip)):
            if computed_transit_trip[index]['date_time'] >= list_car_route[0]['date_time']:
                transit_first_index = index
                break

    car_last_index = len(list_car_route)-1
    transit_last_index = len(computed_transit_trip)-1
    # car fineshed first
    if list_car_route[-1]['date_time'] < computed_transit_trip[-1]['date_time']:
        for index in range(len(computed_transit_trip)):
            if computed_transit_trip[index]['date_time'] <= list_car_route[-1]['date_time']:
                transit_last_index = index
            else:
                break
    else: #transit ends first
        for index in range(len(list_car_route)):
            if list_car_route[index]['date_time'] <= computed_transit_trip[-1]['date_time']:
                car_last_index = index
            else:
                break

    overlaped_car_indexes = (car_first_index, car_last_index)
    overlaped_transit_indexes = (transit_first_index, transit_last_index)

    return overlaped_car_indexes, overlaped_transit_indexes

def integration_positions(list_car_trip, list_transit_trip):
    shortest_distance = maxint
    transit_integration_index = 0
    car_integration_index = 0
    for transit_pos in range(len(list_transit_trip)):
        for car_pos in range(len(list_car_trip)):
            distance = vincenty((list_transit_trip[transit_pos]['longitude'], list_transit_trip[transit_pos]['latitude']),\
            (list_car_trip[car_pos]['longitude'], list_car_trip[car_pos]['latitude'])).meters
            if distance < shortest_distance:
                shortest_distance = distance
                transit_integration_index = transit_pos
                car_integration_index = car_pos

    return {'shortest_distance': shortest_distance, 'transit_index': transit_integration_index,\
    'car_index': car_integration_index}

def group_df_rows(df, key_label, sort_by_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    if sort_by_label:
        for key, list_dict in dict_grouped.iteritems():
            dict_grouped[key] = sorted(list_dict, key=lambda pos: pos[sort_by_label])
    return dict_grouped

def add_date_time(origin_time, list_steps):
    list_position_time = []
    for step in list_steps:
        step_time = origin_time + timedelta(seconds=step['duration'])
        step['date_time'] = step_time
    return list_steps

def list_modes(mode_codes):
    if ',' in mode_codes:
    	list_mode_codes = [int(code) for code in mode_codes.split(',')]
    else:
    	list_mode_codes = [int(mode_codes)]
    return list_mode_codes

def car_trips_happening(dict_car_trips, initial_time, last_time):
    list_car_keys = []
    for key, list_trip in dict_car_trips.iteritems():
        if initial_time < list_trip[-1]['date_time'] and list_trip[0]['date_time'] < last_time:
            list_car_keys.append(key)
    return list_car_keys

def find_best_integration(computed_transit_trip, computed_car_trip, router_id):
    otp = OTP_routing(router_id)

    for transit_position in computed_transit_trip[:-1]:
        for car_position in computed_car_trip[:-1]:

            integration_car_trip = otp.route_positions(car_position['latitude'], car_position['longitude'],\
            transit_position['latitude'], transit_position['longitude'], 'CAR', car_position['date_time'])

            car_arrival_time_transit_stop = integration_car_trip[-1]['date_time']
            car_arrival_time_destination = computed_car_trip[-1]['date_time']
            transit_arrival_time_stop = transit_position['date_time']
            transit_passenger_destination_time = computed_transit_trip[-1]['date_time']

            car_departure_time_transit_stop = car_arrival_time_transit_stop
            if transit_arrival_time_stop > car_arrival_time_transit_stop:
                car_departure_time_transit_stop = transit_arrival_time_stop

            transit_route_by_car = otp.route_positions(transit_position['latitude'], transit_position['longitude'],\
            computed_transit_trip[-1]['latitude'], computed_transit_trip[-1]['longitude'], 'CAR', car_departure_time_transit_stop)

            transit_route_by_car_destination_time = transit_route_by_car[-1]['date_time']

            if car_departure_time_transit_stop < car_arrival_time_destination\
            and transit_route_by_car_destination_time < transit_passenger_destination_time:
                print 'There is an integration'
                print transit_route_by_car_destination_time
                print transit_passenger_destination_time
                car_integration_time = (car_departure_time_transit_stop - car_position['date_time']).total_seconds()
                print car_integration_time/60
                # print car_arrival_time_transit_stop
                # print transit_position
                # print car_position



# format modes
list_car_modes = list_modes(car_mode_codes)
list_transit_modes = list_modes(transit_mode_codes)
list_all_modes = list_car_modes + list_transit_modes

# read survey trips
df_trips = pd.read_csv(survey_trips_path)
df_trips = df_trips[df_trips['MODE_G10'].isin(list_all_modes)]
df_trips['date_time_origin'] = pd.to_datetime(df_trips['date_time_origin'])
df_trips['date_time_destination'] = pd.to_datetime(df_trips['date_time_destination'])

# read car trips
df_car_trips = pd.read_csv(car_trips_path)
del df_car_trips['id']
df_car_trips['date_time'] = pd.to_datetime(df_car_trips['date_time'])
# print df_car_trips

# read transit trips
df_transit_trips = pd.read_csv(transit_trips_path)
del df_transit_trips['id']
df_transit_trips['date_time'] = pd.to_datetime(df_transit_trips['date_time'])
# print df_transit_trips

dict_car_trips = group_df_rows(df_car_trips, 'sampn_perno_tripno', 'date_time')
dict_transit_trips = group_df_rows(df_transit_trips, 'sampn_perno_tripno', 'date_time')
# print len(dict_car_trips)
# print len(dict_transit_trips)

# for each transit passenger trip,
# find similar car trips that would help the transit passenger arrive at their destination earlier
for transit_trip_id, computed_transit_trip in dict_transit_trips.iteritems():

    # do not consider walking positions after last alighting stop as integrable positions
    last_transit_index = len(computed_transit_trip)-1
    for index in reversed(xrange(len(computed_transit_trip))):
        if type(computed_transit_trip[index]['stop_id']) != float:
            last_transit_index = index
            break

    integrable_transit_trip = computed_transit_trip[0:last_transit_index+1]

    departure_transit_passenger_time = computed_transit_trip[0]['date_time']
    computed_transit_destination_time = computed_transit_trip[-1]['date_time']
    last_integrable_transit_position_time = integrable_transit_trip[-1]['date_time']

    # find car trips that could help the transit passenger arrive at his destination earlier
    list_ids_car_trips_happening = car_trips_happening(dict_car_trips, departure_transit_passenger_time, last_integrable_transit_position_time)
    print list_ids_car_trips_happening
    dict_car_trips_happening = {key: dict_car_trips[key] for key in list_ids_car_trips_happening}

    # if there is at least a match
    if len(dict_car_trips_happening) > 0:

        # find the best integration point if it exists
        for car_trip_id, computed_car_trip in dict_car_trips_happening.iteritems():
            print transit_trip_id, car_trip_id
            find_best_integration(computed_transit_trip, computed_car_trip, router_id)

        print len(dict_car_trips_happening)
        break
stop

# match routes
# iterating over car passenger routes
list_matches = []
count_matching = 0
for car_sampn_perno_tripno, computed_car_trip in dict_car_trips.iteritems():

    informed_car_trip = trip_from_sampn_perno_tripno(df_trips, car_sampn_perno_tripno)
    informed_car_pickup_time = informed_car_trip['date_time_origin'].iloc[0]
    informed_car_dropoff_time = informed_car_trip['date_time_destination'].iloc[0]

    computed_trip_duration = computed_car_trip[-1]['duration']
    computed_car_passenger_dropoff_time = informed_car_pickup_time + timedelta(seconds=computed_trip_duration)

    # iterating over transit passenger routes
    for transit_sampn_perno_tripno, computed_transit_trip in dict_transit_trips.iteritems():

        # do not consider walking positions after alighting stop
        first_walking = True
        first_alight_walking_pos = -1
        for transit_pos in range(len(computed_transit_trip)):
            if type(computed_transit_trip[transit_pos]['stop_id']) == str:
                first_walking = False
            elif first_walking == False:
                first_alight_walking_pos = transit_pos
                break

        computed_transit_trip = computed_transit_trip[:first_alight_walking_pos]

        # get informed travel data
        informed_transit_trip = trip_from_sampn_perno_tripno(df_trips, transit_sampn_perno_tripno)
        informed_transit_origin_time = informed_transit_trip['date_time_origin'].iloc[0]

        computed_transit_destination_time = computed_transit_trip[-1]['date_time']

        # verify if car route and transit route overlap each other temporally
        if informed_transit_origin_time < computed_car_passenger_dropoff_time\
        and informed_car_pickup_time < computed_transit_destination_time:

            # reconstruct car temporal routes
            computed_car_trip = add_date_time(informed_car_pickup_time, computed_car_trip)

            # compute overlaping of routes
            overlaped_car_indexes, overlaped_transit_indexes = time_overlaped_routes(computed_car_trip,\
            computed_transit_trip)

            overlaped_transit_time = computed_transit_trip[overlaped_transit_indexes[0]: overlaped_transit_indexes[1]+1]
            overlaped_car_time = computed_car_trip[overlaped_car_indexes[0]: overlaped_car_indexes[1]+1]

            # verify if car route is close to transit route
            dict_shortest_distance = integration_positions(overlaped_car_time, overlaped_transit_time)
            shortest_distance = dict_shortest_distance['shortest_distance']

            # print ''
            # print computed_car_trip
            # print overlaped_transit_indexes
            # print overlaped_car_time
            # print computed_car_trip[overlaped_car_indexes[0]], computed_car_trip[overlaped_car_indexes[1]]

            # if overlaped_transit_indexes[0] == overlaped_transit_indexes[1]:
            #     car_integration_last_distance = overlaped_transit_indexes[0]
            # else:
            car_integration_last_distance = overlaped_car_time[-1]['distance'] - overlaped_car_time[0]['distance']

            if shortest_distance < car_integration_last_distance:

                real_transit_intergration_index = overlaped_transit_indexes[0] + dict_shortest_distance['transit_index']
                real_car_intergration_index = overlaped_car_indexes[0] + dict_shortest_distance['car_index']
                transit_integration_pos = computed_transit_trip[real_transit_intergration_index]
                car_integration_pos = computed_car_trip[real_car_intergration_index]

                transit_origin_integration = computed_transit_trip[:real_transit_intergration_index+1]
                car_origin_integration = computed_car_trip[:real_car_intergration_index+1]

                # compute walking distance and duration
                # compute transit distance and duration
                first_origin_walking = {}
                last_origin_walking = {}
                first_transit_travel = {}
                last_transit_travel = {}
                first_destination_walking = {}
                last_destination_walking = {}
                boarded = False
                for current_position in transit_origin_integration:
                    if (type(current_position['stop_id']) == float and math.isnan(current_position['stop_id'])) == False:
                        boarded = True

                    # origin-boarding positions
                    if boarded == False and current_position['stop_id']:
                        if len(first_origin_walking) == 0:
                            first_origin_walking = current_position.copy()
                        last_origin_walking = current_position.copy()

                    # traveling positions
                    elif boarded == True and type(current_position['stop_id']) == str:
                        if len(first_transit_travel) == 0:
                            first_transit_travel = current_position.copy()
                        last_transit_travel = current_position.copy()

                    # alighting-destination positions
                    elif boarded == True:
                        if len(first_destination_walking) == 0:
                            first_destination_walking = current_position.copy()
                        last_destination_walking = current_position.copy()

                list_route_match = []
                if len(first_origin_walking) > 0:
                    first_origin_walking['sequence'] = 1
                    last_origin_walking['sequence'] = 2
                    first_origin_walking['match_id'] = count_matching
                    last_origin_walking['match_id'] = count_matching
                    first_origin_walking['sampn_perno_tripno'] = transit_sampn_perno_tripno
                    last_origin_walking['sampn_perno_tripno'] = transit_sampn_perno_tripno
                    list_matches.append(first_origin_walking)
                    list_matches.append(last_origin_walking)

                    list_route_match.append(first_origin_walking)
                    list_route_match.append(last_origin_walking)

                if len(first_transit_travel) > 0:
                    first_transit_travel['sequence'] = 3
                    last_transit_travel['sequence'] = 4
                    first_transit_travel['match_id'] = count_matching
                    last_transit_travel['match_id'] = count_matching
                    first_transit_travel['sampn_perno_tripno'] = transit_sampn_perno_tripno
                    last_transit_travel['sampn_perno_tripno'] = transit_sampn_perno_tripno
                    list_matches.append(first_transit_travel)
                    list_matches.append(last_transit_travel)

                    list_route_match.append(first_transit_travel)
                    list_route_match.append(last_transit_travel)

                if len(first_destination_walking) > 0:
                    first_destination_walking['sequence'] = 5
                    last_destination_walking['sequence'] = 6
                    first_destination_walking['match_id'] = count_matching
                    last_destination_walking['match_id'] = count_matching
                    first_destination_walking['sampn_perno_tripno'] = transit_sampn_perno_tripno
                    last_destination_walking['sampn_perno_tripno'] = transit_sampn_perno_tripno
                    list_matches.append(first_destination_walking)
                    list_matches.append(last_destination_walking)

                    list_route_match.append(first_destination_walking)
                    list_route_match.append(last_destination_walking)


                first_car_travel = car_origin_integration[0].copy()
                last_car_travel = car_origin_integration[-1].copy()
                first_car_travel['stop_id'] = ''
                last_car_travel['stop_id'] = ''
                first_car_travel['sequence'] = 7
                last_car_travel['sequence'] = 8
                first_car_travel['match_id'] = count_matching
                last_car_travel['match_id'] = count_matching
                first_car_travel['sampn_perno_tripno'] = car_sampn_perno_tripno
                last_car_travel['sampn_perno_tripno'] = car_sampn_perno_tripno
                list_matches.append(first_car_travel)
                list_matches.append(last_car_travel)

                list_route_match.append(first_car_travel)
                list_route_match.append(last_car_travel)

                count_matching += 1

                for route in list_route_match:
                    print route['match_id'], route['sampn_perno_tripno'], route['sequence']

                print ''

                # print '=>Subway trip', transit_sampn_perno_tripno
                # print first_origin_walking
                # print last_origin_walking
                # print first_transit_travel
                # print last_transit_travel
                # print first_destination_walking
                # print last_destination_walking
                #
                # print '=>Taxi trip', car_sampn_perno_tripno
                # print first_car_travel
                # print last_car_travel

                print '============================='

    # if count_matching > 6:
    #     break

df_matches = pd.DataFrame(list_matches)
df_matches = df_matches[['match_id', 'sampn_perno_tripno', 'sequence', 'date_time', 'distance',\
'longitude', 'latitude', 'stop_id']]
df_matches = df_matches.sort_values(by=['match_id', 'sequence'])
df_matches.to_csv(result_path, index=False)
