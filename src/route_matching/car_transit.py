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

# survey_trips_path = argv[1]
transit_trips_path = argv[1]
# transit_mode_codes = argv[2]
car_trips_path = argv[2]
# car_mode_codes = argv[4]
router_id = argv[3]
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

def gtfs_date_time(date_time, gtfs_year):
    # find equivalent day in the GTFS's year
    gtfs_day = datetime(gtfs_year, date_time.month, 1)
    while gtfs_day.weekday() != date_time.weekday():
        gtfs_day += timedelta(days=1)
    new_date_time = datetime.combine(gtfs_day.date(), date_time.time())
    return new_date_time

def integration_position_times(computed_transit_trip, computed_car_trip, router_id):
    otp = OTP_routing(router_id)

    list_possible_integrations = []
    best_saving_time = -maxint

    computed_car_destination = computed_car_trip[-1]
    computed_transit_destination = computed_transit_trip[-1]

    for transit_position in computed_transit_trip[:-1]:
        for car_position in computed_car_trip[:-1]:

            if transit_position['date_time'] < computed_car_destination['date_time']\
            and car_position['date_time'] < computed_transit_destination['date_time']:

                # integration_car -> integration_transit
                integration_car_trip = otp.route_positions(car_position['latitude'], car_position['longitude'],\
                transit_position['latitude'], transit_position['longitude'], 'CAR', car_position['date_time'])
                if len(integration_car_trip) == 0: continue

                car_arrival_time_transit_stop = integration_car_trip[-1]['date_time']
                transit_arrival_time_stop = transit_position['date_time']

                car_passenger_destination_time = computed_car_destination['date_time']
                transit_passenger_destination_time = computed_transit_destination['date_time']

                car_departure_time_transit_stop = car_arrival_time_transit_stop
                if transit_arrival_time_stop > car_arrival_time_transit_stop:
                    car_departure_time_transit_stop = transit_arrival_time_stop

                if car_departure_time_transit_stop < car_passenger_destination_time:

                    # integration_transit -> destination_transit
                    integration_transit_destination_trip = otp.route_positions(transit_position['latitude'], transit_position['longitude'],\
                    computed_transit_destination['latitude'], computed_transit_destination['longitude'], 'CAR', car_departure_time_transit_stop)
                    if len(integration_transit_destination_trip) == 0: continue
                    integration_transit_destination_time = integration_transit_destination_trip[-1]['date_time']

                    # integration_transit -> destination_car
                    integration_car_destination_trip = otp.route_positions(transit_position['latitude'], transit_position['longitude'],\
                    computed_car_destination['latitude'], computed_car_destination['longitude'], 'CAR', car_departure_time_transit_stop)
                    if len(integration_car_destination_trip) == 0: continue
                    integration_car_destination_time = integration_car_destination_trip[-1]['date_time']

                    if integration_car_destination_time < integration_transit_destination_time:

                        # destination_car -> destination_transit
                        destination_car_destination_transit_trip = otp.route_positions(integration_car_destination_trip[-1]['latitude'],\
                        integration_car_destination_trip[-1]['longitude'], integration_transit_destination_trip[-1]['latitude'],\
                        integration_transit_destination_trip[-1]['longitude'], 'CAR', integration_car_destination_time)
                        if len(destination_car_destination_transit_trip) == 0: continue
                        integration_transit_destination_time = destination_car_destination_transit_trip[-1]['date_time']

                    if integration_transit_destination_time < transit_passenger_destination_time:

                        # car wasting time
                        if integration_car_destination_time >= integration_transit_destination_time:
                            # destination_transit -> destination_car
                            destination_transit_destination_car_trip = otp.route_positions(integration_transit_destination_trip[-1]['latitude'],\
                            integration_transit_destination_trip[-1]['longitude'], integration_car_destination_trip[-1]['latitude'],\
                            integration_car_destination_trip[-1]['longitude'],  'CAR', integration_transit_destination_time)
                            if len(destination_transit_destination_car_trip) == 0: continue
                            integration_car_destination_time = destination_transit_destination_car_trip[-1]['date_time']

                        # print 'There is an integration'
                        # # print transit_position
                        # # print car_position
                        # print car_departure_time_transit_stop
                        # print transit_passenger_destination_time
                        # print integration_transit_destination_time
                        transit_saving_time = (transit_passenger_destination_time - integration_transit_destination_time).total_seconds()/60
                        # print 'transit_saving_time', transit_saving_time
                        # print integration_car_destination_time
                        # print car_passenger_destination_time
                        car_extra_time = (integration_car_destination_time - car_passenger_destination_time).total_seconds()/60
                        # print 'car_extra_time', car_extra_time
                        dict_costs = {'car':{'trip_sequence': car_position['trip_sequence'], 'pos_sequence': car_position['pos_sequence'],\
                        'destination_time': integration_car_destination_time},\
                        'transit': {'trip_sequence': transit_position['trip_sequence'], 'pos_sequence': transit_position['pos_sequence'],\
                        'destination_time': integration_transit_destination_time},\
                        'car_arrival_time_transit_stop': car_arrival_time_transit_stop}
                        list_possible_integrations.append(dict_costs)
                        # print '======================================'
            #         else:
            #             print 'transit arrive at his destination first'
            #
            #     else:
            #         print 'car arrive at destination first'
            # else:
            #     print 'there is not enough time to get the transit passenter'
    return list_possible_integrations

def is_date_time_consistet(list_trip):
    for index in range(1, len(list_trip)):
        diff_date_time = (list_trip[index]['date_time'] - list_trip[index-1]['date_time']).total_seconds()
        if diff_date_time < 0:
            print 'date_time not consistent'
            return False
    return True

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

dict_car_trips = group_df_rows(df_car_trips, 'sampn_perno_tripno')
dict_transit_trips = group_df_rows(df_transit_trips, 'sampn_perno_tripno')
# print len(dict_car_trips)
# print len(dict_transit_trips)

# for each transit passenger trip,
# find similar car trips that would help the transit passenger arrive at their destination earlier
list_matches = []
for transit_trip_id, computed_transit_trip in dict_transit_trips.iteritems():
    #  if transit_trip_id != '6007368_2_2': continue
    if is_date_time_consistet(computed_transit_trip) == False: continue

    print '\ntransit_trip_id', transit_trip_id


    # do not consider walking positions after last alighting stop as integrable positions
    # last_transit_index = len(computed_transit_trip)-1
    # for index in reversed(xrange(len(computed_transit_trip))):
    #     if type(computed_transit_trip[index]['stop_id']) != float:
    #         last_transit_index = index
    #         break
    # integrable_transit_trip = computed_transit_trip[0:last_transit_index+1]

    departure_transit_passenger_time = computed_transit_trip[0]['date_time']
    computed_transit_destination_time = computed_transit_trip[-1]['date_time']
    # last_integrable_transit_position_time = integrable_transit_trip[-1]['date_time']

    # find car trips that could help the transit passenger arrive at his destination earlier
    list_ids_car_trips_happening = car_trips_happening(dict_car_trips, departure_transit_passenger_time, computed_transit_destination_time)
    # print 'car_trips_happening', list_ids_car_trips_happening
    dict_car_trips_happening = {key: dict_car_trips[key] for key in list_ids_car_trips_happening}

    # if there is at least a match
    if len(dict_car_trips_happening) > 0:

        # find the best integration point if it exists
        for car_trip_id, computed_car_trip in dict_car_trips_happening.iteritems():
            if is_date_time_consistet(computed_car_trip) == False: continue
            print 'car_trip_id', car_trip_id

            print 'car_trip', computed_car_trip[0]['date_time'], computed_car_trip[-1]['date_time']
            print 'transit_trip', computed_transit_trip[0]['date_time'], computed_transit_trip[-1]['date_time']

            integration_times = integration_position_times(computed_transit_trip, computed_car_trip, router_id)

            if len(integration_times) > 0:
                # earlier_transit_arrival_time = integration_times[0]['transit']['destination_time']
                dict_earlier_transit_arrival_time = integration_times[0]

                for dict_integration in integration_times:
                    dict_match = {'transit_trip_id': transit_trip_id, 'car_trip_id': car_trip_id,\
                    'car_trip_sequence': dict_integration['car']['trip_sequence'],\
                    'car_pos_sequence': dict_integration['car']['pos_sequence'],\
                    'car_destination_time': dict_integration['car']['destination_time'],\
                    'transit_trip_sequence': dict_integration['transit']['trip_sequence'],\
                    'transit_pos_sequence': dict_integration['transit']['pos_sequence'],\
                    'transit_destination_time': dict_integration['transit']['destination_time'],\
                    'car_arrival_time_transit_stop': dict_integration['car_arrival_time_transit_stop']}
                    list_matches.append(dict_match)
                #     print 'car_destination_time', dict_integration['car']['destination_time']
                #     print 'transit_destination_time', dict_integration['transit']['destination_time']
                # stop

            else:
                print 'there is not any integration station' #stop

    else:
        print 'there is not any overlaping'

    # if len(dict_car_trips_happening)>1:
    #     break

df_matches = pd.DataFrame(list_matches)
print df_matches
df_matches = df_matches[['transit_trip_id', 'car_trip_id', 'car_trip_sequence','car_pos_sequence','car_destination_time',\
'transit_trip_sequence', 'transit_pos_sequence', 'transit_destination_time','car_arrival_time_transit_stop']]
# df_matches = df_matches.sort_values(by=['match_id', 'sequence'])
df_matches.to_csv(result_path, index=False)
