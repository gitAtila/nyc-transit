'''
    Analyse estimatives of time from transit car matching
'''

from sys import argv, maxint
import pandas as pd
import numpy as np

from geopy.distance import vincenty

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from statsmodels.distributions.empirical_distribution import ECDF

transit_trips_path = argv[1]
car_trips_path = argv[2]
matching_trips_path = argv[3]
chart_path = argv[4]

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

def nyc_transit_taxi_shared_costs(date_time_origin, origin_distance, origin_stopped_time,\
integration_distance, integration_stopped_time, waiting_time_stop, shared_distance, shared_stopped_time,\
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

    taxi_passenger_cost = initial_cost/2
    transit_passenger_cost = initial_cost/2

    price_per_meter = mile_in_meters * rate_per_mile

    # origin-acceptance
    taxi_passenger_cost += origin_distance * price_per_meter
    taxi_passenger_cost += ((origin_stopped_time/60) * rate_per_minute_stopped)

    # acceptance-integration
    taxi_passenger_cost += integration_distance * price_per_meter
    taxi_passenger_cost += ((integration_stopped_time/60) * rate_per_minute_stopped)

    # integration-first_destination
    taxi_passenger_cost += (shared_distance * price_per_meter)/2
    taxi_passenger_cost += (((waiting_time_stop + shared_stopped_time)/60) * rate_per_minute_stopped)/2

    transit_passenger_cost += (shared_distance * price_per_meter)/2
    transit_passenger_cost += (((waiting_time_stop + shared_stopped_time)/60) * rate_per_minute_stopped)/2

    if transit_destination_first == True:
        taxi_passenger_cost += destinations_distance * price_per_meter
        taxi_passenger_cost += (destinations_stopped_time/60) * rate_per_minute_stopped
    else:
        transit_passenger_cost += destinations_distance * price_per_meter
        transit_passenger_cost += (destinations_stopped_time/60) * rate_per_minute_stopped

    return transit_passenger_cost, taxi_passenger_cost

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

def group_list_dict(list_dict, key_label):
    dict_grouped = dict()
    for item in list_dict:
        key = item[key_label]
        del item[key_label]
        dict_grouped.setdefault(key, []).append(item)
    return dict_grouped

def integrations_maximum_transit_saving_time(df_transit_trips, df_car_trips, dict_transit_taxisharing):
    # get integrations where the saving time for transit passenger is the most
    list_best_integrations = []
    for transit_trip_id, list_integrations in dict_transit_taxisharing.iteritems():

        transit_trip = df_transit_trips[df_transit_trips['sampn_perno_tripno'] == transit_trip_id]
        dict_car_taxisharing = group_list_dict(list_integrations, 'car_trip_id')
        # print '\n', transit_trip_id, len(dict_car_taxisharing)

        best_car_saving_time = -maxint
        best_car_integration_position = {}
        for car_trip_id, list_car_integrations in dict_car_taxisharing.iteritems():
            car_trip = df_car_trips[df_car_trips['sampn_perno_tripno'] == car_trip_id]
            # print '\t',car_trip_id, len(list_car_integrations)

            max_saving_time = -maxint
            best_integration_position = {}
            for integration in list_car_integrations:
                transit_saving_time = (transit_trip['date_time'].iloc[-1] - integration['transit_destination_time']).total_seconds()

                if transit_saving_time > max_saving_time:
                    max_saving_time = transit_saving_time
                    integration['transit_trip_id'] = transit_trip_id
                    integration['car_trip_id'] = car_trip_id
                    best_integration_position = integration

            if max_saving_time > best_car_saving_time:
                best_car_saving_time = max_saving_time
                best_car_integration_position = best_integration_position

        list_best_integrations.append(best_car_integration_position)

    return list_best_integrations

def integrations_saving_and_not_cost(df_transit_trips, df_car_trips, list_best_integrations):
    list_good_integrations = []
    list_bad_integrations = []
    for integration in list_best_integrations:
        # print integration['transit_trip_id'], integration['car_trip_id']

        transit_trip = df_transit_trips[df_transit_trips['sampn_perno_tripno'] == integration['transit_trip_id']]
        transit_acceptance = transit_trip[(transit_trip['trip_sequence'] == integration['transit_trip_sequence'])\
        & (transit_trip['pos_sequence'] == integration['transit_pos_sequence'])].iloc[0].T.to_dict()

        car_trip = df_car_trips[df_car_trips['sampn_perno_tripno'] == integration['car_trip_id']]
        car_acceptance = car_trip[(car_trip['trip_sequence'] == integration['car_trip_sequence'])\
        & (car_trip['pos_sequence'] == integration['car_pos_sequence'])].iloc[0].T.to_dict()

        taxi_date_time_origin = car_trip['date_time'].iloc[0]
        taxi_distance = car_trip['distance'].iloc[-1]

        # print taxi_date_time_origin, taxi_date_time_origin.hour, taxi_date_time_origin.weekday()
        # print taxi_distance

        taxi_private_cost = nyc_taxi_cost(taxi_date_time_origin, taxi_distance, 0)

        taxi_waiting_time_stop = 0
        if integration['car_arrival_time_transit_stop'] < transit_acceptance['date_time']:
            taxi_waiting_time_stop += (transit_acceptance['date_time'] - integration['car_arrival_time_transit_stop']).total_seconds()

        start_integration_distance = car_acceptance['distance']
        integration_distance = integration['integration_distance']
        shared_distance = integration['shared_distance']
        destinations_distance = integration['destinations_distance']

        transit_destination_first = True
        if integration['car_destination_time'] < integration['transit_destination_time']:
            transit_destination_first = False

        total_distance = start_integration_distance + integration_distance + shared_distance + destinations_distance

        total_integrated_cost = nyc_taxi_cost(taxi_date_time_origin, total_distance, taxi_waiting_time_stop)

        transit_shared_cost, taxi_shared_cost = nyc_transit_taxi_shared_costs(taxi_date_time_origin,start_integration_distance, 0,\
        integration_distance, 0, taxi_waiting_time_stop, shared_distance, 0, transit_destination_first, destinations_distance, 0)

        if taxi_shared_cost <= taxi_private_cost:
            list_good_integrations.append(integration)
        else:
            list_bad_integrations.append(integration)

    return list_good_integrations, list_bad_integrations

def segments_duration(df_transit_trips, df_car_trips, list_best_integrations):

    list_transit_origin_acceptance = []
    list_car_origin_acceptance = []
    list_car_acceptance_integration = []
    list_car_integration_destination = []
    list_car_between_destinations = []

    for integration in list_best_integrations:
        # print integration['transit_trip_id'], integration['car_trip_id']

        transit_trip = df_transit_trips[df_transit_trips['sampn_perno_tripno'] == integration['transit_trip_id']]
        transit_acceptance = transit_trip[(transit_trip['trip_sequence'] == integration['transit_trip_sequence'])\
        & (transit_trip['pos_sequence'] == integration['transit_pos_sequence'])].iloc[0].T.to_dict()

        car_trip = df_car_trips[df_car_trips['sampn_perno_tripno'] == integration['car_trip_id']]
        car_acceptance = car_trip[(car_trip['trip_sequence'] == integration['car_trip_sequence'])\
        & (car_trip['pos_sequence'] == integration['car_pos_sequence'])].iloc[0].T.to_dict()

        taxi_date_time_origin = car_trip['date_time'].iloc[0]
        taxi_distance = car_trip['distance'].iloc[-1]

        list_transit_origin_acceptance.append((transit_acceptance['date_time'] - transit_trip.iloc[0]['date_time']).total_seconds()/60)
        list_car_origin_acceptance.append((car_acceptance['date_time'] - car_trip.iloc[0]['date_time']).total_seconds()/60)
        list_car_acceptance_integration.append((integration['car_arrival_time_transit_stop'] - car_acceptance['date_time']).total_seconds()/60)

        if integration['car_destination_time'] < integration['transit_destination_time']:
            first_destination_time = integration['car_destination_time']
            last_destination_time = integration['transit_destination_time']
        else:
            first_destination_time = integration['transit_destination_time']
            last_destination_time = integration['car_destination_time']

        list_car_integration_destination.append((first_destination_time - integration['car_arrival_time_transit_stop']).total_seconds()/60)
        list_car_between_destinations.append((last_destination_time - first_destination_time).total_seconds()/60)

    return list_transit_origin_acceptance, list_car_origin_acceptance, list_car_acceptance_integration, list_car_integration_destination,\
        list_car_between_destinations

def compute_walking_transit_distances(df_transit_positions, dict_transit_acceptance_position):
    list_origin_acceptance = []
    for index, position in df_transit_positions.iterrows():
        list_origin_acceptance.append(position.T.to_dict())
        if position['trip_sequence'] == dict_transit_acceptance_position['trip_sequence']\
        and position['pos_sequence'] == dict_transit_acceptance_position['pos_sequence']:
            break

    list_walking_positions = []
    list_transit_positions = []
    for position in list_origin_acceptance:
        # print position
        if type(position['stop_id']) == float and np.isnan(position['stop_id']) == True\
        and np.isnan(position['distance']) == False:
            list_walking_positions.append(position)
        else:
            list_transit_positions.append(position)

    # print list_transit_positions
    dict_walking_positions = group_list_dict(list_walking_positions, 'trip_sequence')
    dict_transit_positions = group_list_dict(list_transit_positions, 'trip_sequence')

    walking_distance = 0
    for trip_id, walking_positions in dict_walking_positions.iteritems():
        walking_distance += max(position['distance'] for position in walking_positions)
    # print 'walking_distance', walking_distance

    transit_distance = 0
    for trip_id, transit_positions in dict_transit_positions.iteritems():
        trip_distance = 0
        previous_position = transit_positions[0]
        for current_position in transit_positions[1:]:
            trip_distance += vincenty((previous_position['latitude'], previous_position['latitude']),\
            (current_position['latitude'], current_position['latitude'])).meters
            previous_position = current_position
        transit_distance += trip_distance
    # print 'transit_distance', transit_distance

    return walking_distance, transit_distance

def segments_distance(df_transit_trips, df_car_trips, list_best_integrations):

    list_transit_origin_acceptance = []
    list_car_origin_acceptance = []
    list_car_acceptance_integration = []
    list_car_integration_destination = []
    list_car_between_destinations = []

    for integration in list_best_integrations:
        # print integration['transit_trip_id'], integration['car_trip_id']

        transit_trip = df_transit_trips[df_transit_trips['sampn_perno_tripno'] == integration['transit_trip_id']]
        transit_acceptance = transit_trip[(transit_trip['trip_sequence'] == integration['transit_trip_sequence'])\
        & (transit_trip['pos_sequence'] == integration['transit_pos_sequence'])].iloc[0].T.to_dict()

        car_trip = df_car_trips[df_car_trips['sampn_perno_tripno'] == integration['car_trip_id']]
        car_acceptance = car_trip[(car_trip['trip_sequence'] == integration['car_trip_sequence'])\
        & (car_trip['pos_sequence'] == integration['car_pos_sequence'])].iloc[0].T.to_dict()

        taxi_date_time_origin = car_trip['date_time'].iloc[0]
        taxi_distance = car_trip['distance'].iloc[-1]

        transit_walking_distance, transit_vehicle_distance = compute_walking_transit_distances(transit_trip, transit_acceptance)
        transit_acceptance_distance = transit_walking_distance + transit_vehicle_distance

        # taxi_waiting_time_stop = 0
        # if integration['car_arrival_time_transit_stop'] < transit_acceptance['date_time']:
        #     taxi_waiting_time_stop += (transit_acceptance['date_time'] - integration['car_arrival_time_transit_stop']).total_seconds()

        list_transit_origin_acceptance.append(transit_acceptance_distance/1000)
        list_car_origin_acceptance.append(car_acceptance['distance']/1000)
        list_car_acceptance_integration.append(integration['integration_distance']/1000)
        list_car_integration_destination.append(integration['shared_distance']/1000)
        list_car_between_destinations.append(integration['destinations_distance']/1000)

    return list_transit_origin_acceptance, list_car_origin_acceptance, list_car_acceptance_integration, list_car_integration_destination,\
        list_car_between_destinations

def negative_to_zero(list_numbers):
    new_list = []
    for number in list_numbers:
        if number < 0:
            new_list.append(0)
        else:
            new_list.append(number)
    return new_list

def plot_cdf_segments(list_transit_origin_acceptance, list_car_origin_acceptance, list_car_acceptance_integration,\
list_car_integration_destination, list_car_between_destinations, x_axis_label, chart_name):

    list_transit_origin_acceptance = negative_to_zero(list_transit_origin_acceptance)
    list_car_origin_acceptance = negative_to_zero(list_car_origin_acceptance)
    list_car_acceptance_integration = negative_to_zero(list_car_acceptance_integration)
    list_car_integration_destination = negative_to_zero(list_car_integration_destination)
    list_car_between_destinations = negative_to_zero(list_car_between_destinations)

    list_transit_origin_acceptance.sort()
    list_car_origin_acceptance.sort()
    list_car_acceptance_integration.sort()
    list_car_integration_destination.sort()
    list_car_between_destinations.sort()

    # print min(list_transit_origin_acceptance), max(list_transit_origin_acceptance)
    # print list_transit_origin_acceptance

    ecdf_transit_origin_acceptance = ECDF(list_transit_origin_acceptance)
    ecdf_car_origin_acceptance = ECDF(list_car_origin_acceptance)
    ecdf_car_acceptance_integration = ECDF(list_car_acceptance_integration)
    ecdf_car_integration_destination = ECDF(list_car_integration_destination)
    ecdf_car_between_destinations = ECDF(list_car_between_destinations)

    fig, ax = plt.subplots()
    plt.plot(ecdf_transit_origin_acceptance.x, ecdf_transit_origin_acceptance.y, label='transit origin-acceptance')
    plt.plot(ecdf_car_origin_acceptance.x, ecdf_car_origin_acceptance.y, label='car origin-acceptance')
    plt.plot(ecdf_car_acceptance_integration.x, ecdf_car_acceptance_integration.y, label='car acceptance-integration')
    plt.plot(ecdf_car_integration_destination.x, ecdf_car_integration_destination.y, label='car integration-destination')
    plt.plot(ecdf_car_between_destinations.x, ecdf_car_between_destinations.y, label='car between-destinations')

    # ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
    plt.grid()
    plt.legend(loc=4)
    # ax.set_title('saturday')
    ax.set_xlabel(x_axis_label)
    ax.set_ylabel('CDF')
    plt.tight_layout()
    fig.savefig(chart_name)

def plot_cdf_two_curves(list_curve_1, list_curve_2, label_curve_1, label_curve_2, x_label, chart_path):
    list_curve_1.sort()
    list_curve_2.sort()

    ecdf_curve_1 = ECDF(list_curve_1)
    ecdf_curve_2 = ECDF(list_curve_2)

    fig, ax = plt.subplots()
    plt.plot(ecdf_curve_1.x, ecdf_curve_1.y, label=label_curve_1)
    plt.plot(ecdf_curve_2.x, ecdf_curve_2.y, label=label_curve_2)

    # ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
    plt.grid()
    plt.legend(loc=4)
    # ax.set_title('saturday')
    ax.set_xlabel(x_label)
    ax.set_ylabel('ECDF')
    plt.tight_layout()
    fig.savefig(chart_path)

def plot_cdf_three_curves(list_curve_1, list_curve_2, list_curve_3, label_curve_1, label_curve_2, label_curve_3, x_label, chart_path):
    list_curve_1.sort()
    list_curve_2.sort()
    list_curve_3.sort()

    ecdf_curve_1 = ECDF(list_curve_1)
    ecdf_curve_2 = ECDF(list_curve_2)
    ecdf_curve_3 = ECDF(list_curve_3)

    fig, ax = plt.subplots()
    plt.plot(ecdf_curve_1.x, ecdf_curve_1.y, label=label_curve_1)
    plt.plot(ecdf_curve_2.x, ecdf_curve_2.y, label=label_curve_2)
    plt.plot(ecdf_curve_3.x, ecdf_curve_3.y, label=label_curve_3)

    # ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
    plt.grid()
    plt.legend(loc=4)
    # ax.set_title('saturday')
    ax.set_xlabel(x_label)
    ax.set_ylabel('ECDF')
    plt.tight_layout()
    fig.savefig(chart_path)

df_matching_trips = pd.read_csv(matching_trips_path)
df_matching_trips['car_arrival_time_transit_stop'] = pd.to_datetime(df_matching_trips['car_arrival_time_transit_stop'])
df_matching_trips['transit_destination_time'] = pd.to_datetime(df_matching_trips['transit_destination_time'])
df_matching_trips['car_destination_time'] = pd.to_datetime(df_matching_trips['car_destination_time'])

df_transit_trips = pd.read_csv(transit_trips_path)
df_transit_trips['date_time'] = pd.to_datetime(df_transit_trips['date_time'])

df_car_trips = pd.read_csv(car_trips_path)
df_car_trips['date_time'] = pd.to_datetime(df_car_trips['date_time'])

dict_transit_taxisharing = group_df_rows(df_matching_trips, 'transit_trip_id', '')
print len(dict_transit_taxisharing)

list_best_integrations = integrations_maximum_transit_saving_time(df_transit_trips, df_car_trips, dict_transit_taxisharing)

list_good_integrations, list_bad_integrations = integrations_saving_and_not_cost(df_transit_trips, df_car_trips, list_best_integrations)

print 'good integrations', len(list_good_integrations)
print 'bad integrations', len(list_bad_integrations)

# good integrations
list_transit_origin_acceptance, list_car_origin_acceptance, list_car_acceptance_integration, list_car_integration_destination,\
list_car_between_destinations = segments_duration(df_transit_trips, df_car_trips, list_good_integrations)

plot_cdf_segments(list_transit_origin_acceptance, list_car_origin_acceptance, list_car_acceptance_integration,\
list_car_integration_destination, list_car_between_destinations, 'durantion (minutes)', chart_path + 'cdf_good_durations.png')

list_transit_origin_acceptance, list_car_origin_acceptance, list_car_acceptance_integration, list_car_integration_destination,\
list_car_between_destinations = segments_distance(df_transit_trips, df_car_trips, list_good_integrations)

plot_cdf_segments(list_transit_origin_acceptance, list_car_origin_acceptance, list_car_acceptance_integration,\
list_car_integration_destination, list_car_between_destinations, 'distance (km)', chart_path + 'cdf_good_distances.png')

# bad integrations
list_transit_origin_acceptance, list_car_origin_acceptance, list_car_acceptance_integration, list_car_integration_destination,\
list_car_between_destinations = segments_duration(df_transit_trips, df_car_trips, list_bad_integrations)

plot_cdf_segments(list_transit_origin_acceptance, list_car_origin_acceptance, list_car_acceptance_integration,\
list_car_integration_destination, list_car_between_destinations, 'durantion (minutes)', chart_path + 'cdf_bad_durations.png')

list_transit_origin_acceptance, list_car_origin_acceptance, list_car_acceptance_integration, list_car_integration_destination,\
list_car_between_destinations = segments_distance(df_transit_trips, df_car_trips, list_bad_integrations)

plot_cdf_segments(list_transit_origin_acceptance, list_car_origin_acceptance, list_car_acceptance_integration,\
list_car_integration_destination, list_car_between_destinations, 'distance (km)', chart_path + 'cdf_bad_distances.png')
