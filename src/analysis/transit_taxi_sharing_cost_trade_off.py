'''
    Analyse estimatives of time from transit car matching
'''

from sys import argv, maxint
import pandas as pd

import numpy as np

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
transit_destination_first, destinations_distance, destinations_stopped_time, alpha):

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

    taxi_passenger_cost = initial_cost * (1-alpha)
    transit_passenger_cost = initial_cost * (alpha)

    price_per_meter = mile_in_meters * rate_per_mile

    # origin-acceptance
    taxi_passenger_cost += origin_distance * price_per_meter
    taxi_passenger_cost += ((origin_stopped_time/60) * rate_per_minute_stopped)

    # acceptance-integration
    taxi_passenger_cost += integration_distance * price_per_meter# * (1 - alpha)
    taxi_passenger_cost += ((integration_stopped_time/60) * rate_per_minute_stopped)# * (1 - alpha)

    # transit_passenger_cost += integration_distance * price_per_meter * alpha
    # transit_passenger_cost += ((integration_stopped_time/60) * rate_per_minute_stopped) * alpha

    # integration-first_destination
    taxi_passenger_cost += (shared_distance * price_per_meter) * (1 - alpha)
    taxi_passenger_cost += (((waiting_time_stop + shared_stopped_time)/60) * rate_per_minute_stopped) * (1 - alpha)

    transit_passenger_cost += (shared_distance * price_per_meter) * alpha
    transit_passenger_cost += (((waiting_time_stop + shared_stopped_time)/60) * rate_per_minute_stopped) * alpha

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

def list_best_integrations(df_transit_trips, df_car_trips, dict_transit_taxisharing):
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

def taxi_private_cost(list_best_integrations):
    list_car_ids = list(set(df_car_trips['sampn_perno_tripno'].tolist()))
    list_taxi_private_cost = []
    for car_id in [integrations['car_trip_id'] for integrations in list_best_integrations]:
        car_trip = df_car_trips[df_car_trips['sampn_perno_tripno'] == car_id]
        taxi_date_time_origin = car_trip['date_time'].iloc[0]
        taxi_distance = car_trip['distance'].iloc[-1]

        taxi_private_cost = nyc_taxi_cost(taxi_date_time_origin, taxi_distance, 0)
        list_taxi_private_cost.append(taxi_private_cost)

    return list_taxi_private_cost

def transit_taxi_shared_costs(df_transit_trips, df_car_trips, list_best_integrations, alpha):

    list_taxi_private_cost = []
    list_taxi_shared_cost = []
    list_transit_shared_cost = []
    good_integration = 0
    for integration in list_best_integrations:
        # print integration['transit_trip_id'], integration['car_trip_id']

        transit_trip = df_transit_trips[df_transit_trips['sampn_perno_tripno'] == integration['transit_trip_id']]
        transit_posisiton = transit_trip[(transit_trip['trip_sequence'] == integration['transit_trip_sequence'])\
        & (transit_trip['pos_sequence'] == integration['transit_pos_sequence'])].iloc[0].T.to_dict()

        car_trip = df_car_trips[df_car_trips['sampn_perno_tripno'] == integration['car_trip_id']]
        car_posisiton = car_trip[(car_trip['trip_sequence'] == integration['car_trip_sequence'])\
        & (car_trip['pos_sequence'] == integration['car_pos_sequence'])].iloc[0].T.to_dict()

        taxi_date_time_origin = car_trip['date_time'].iloc[0]
        taxi_distance = car_trip['distance'].iloc[-1]

        # print taxi_date_time_origin, taxi_date_time_origin.hour, taxi_date_time_origin.weekday()
        # print taxi_distance

        taxi_private_cost = nyc_taxi_cost(taxi_date_time_origin, taxi_distance, 0)

        taxi_waiting_time_stop = 0
        if integration['car_arrival_time_transit_stop'] < transit_posisiton['date_time']:
            taxi_waiting_time_stop += (transit_posisiton['date_time'] - integration['car_arrival_time_transit_stop']).total_seconds()

        # compute distributions
        start_integration_distance = car_posisiton['distance']
        integration_distance = integration['integration_distance']
        shared_distance = integration['shared_distance']
        destinations_distance = integration['destinations_distance']

        transit_destination_first = True
        if integration['car_destination_time'] < integration['transit_destination_time']:
            transit_destination_first = False

        total_distance = start_integration_distance + integration_distance + shared_distance + destinations_distance

        total_integrated_cost = nyc_taxi_cost(taxi_date_time_origin, total_distance, taxi_waiting_time_stop)

        transit_shared_cost, taxi_shared_cost = nyc_transit_taxi_shared_costs(taxi_date_time_origin,start_integration_distance, 0,\
        integration_distance, 0, taxi_waiting_time_stop, shared_distance, 0, transit_destination_first, destinations_distance, 0, alpha)

        if taxi_shared_cost < taxi_private_cost:
            good_integration += 1

        list_taxi_private_cost.append(taxi_private_cost)
        list_taxi_shared_cost.append(taxi_shared_cost)
        list_transit_shared_cost.append(transit_shared_cost)

    print 'good_integration', good_integration, float(good_integration)/float(len(list_taxi_shared_cost))
    print 'taxi_private_cost', np.mean(list_taxi_private_cost)
    print 'taxi_shared_cost', np.mean(list_taxi_shared_cost)
    print 'transit_shared_cost', np.mean(list_transit_shared_cost)

    return list_transit_shared_cost, list_taxi_shared_cost

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

list_best_integrations = list_best_integrations(df_transit_trips, df_car_trips, dict_transit_taxisharing)

list_taxi_private_cost = taxi_private_cost(list_best_integrations)

alpha_values = [0, 0.25, 0.5, 0.75, 1]

fig_transit, ax_transit = plt.subplots()
fig_car, ax_car = plt.subplots()

for alpha in alpha_values:
    print alpha
    list_transit_shared_cost, list_taxi_shared_cost = transit_taxi_shared_costs(df_transit_trips, df_car_trips, list_best_integrations, alpha)

    list_transit_shared_cost.sort()
    list_taxi_shared_cost.sort()

    ecdf_curve_1 = ECDF(list_transit_shared_cost)
    ecdf_curve_2 = ECDF(list_taxi_shared_cost)

    ax_transit.plot(ecdf_curve_1.x, ecdf_curve_1.y, label=alpha)
    ax_car.plot(ecdf_curve_2.x, ecdf_curve_2.y, label=alpha)

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
ax_transit.grid()
ax_transit.legend(loc=4)
# ax.set_title('saturday')
ax_transit.set_xlabel('dollars')
ax_transit.set_ylabel('ECDF')
# ax_transit.tight_layout()
fig_transit.savefig(chart_path + 'trade_off_transit.png')

#
list_taxi_private_cost.sort()
ecdf_curve = ECDF(list_taxi_private_cost)
ax_car.plot(ecdf_curve.x, ecdf_curve.y, label='private', color='black')

ax_car.grid()
ax_car.legend(loc=4)
# ax.set_title('saturday')
ax_car.set_xlabel('dollars')
ax_car.set_ylabel('ECDF')
# ax_car.tight_layout()
fig_car.savefig(chart_path + 'trade_off_car.png')

# plot_cdf_two_curves(list_taxi_private_cost, list_taxi_shared_cost, 'taxi private cost', 'taxi shared cost', 'dollars',\
# chart_path + 'cdf_taxi_costs.png')
#
# plot_cdf_three_curves(list_taxi_private_cost, list_taxi_shared_cost, list_transit_shared_cost, 'taxi private cost',\
# 'taxi shared cost', 'transit shared cost', 'dollars', chart_path + 'cdf_taxi_transit_costs.png')