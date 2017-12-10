'''
    Analyse estimatives of time from transit car matching
'''

from sys import argv, maxint
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from statsmodels.distributions.empirical_distribution import ECDF

transit_trips_path = argv[1]
car_trips_path = argv[2]
matching_trips_path = argv[3]
chart_path = argv[4]

def nyc_taxi_cost(date_time_origin, trip_distance_meters, stopped_duration_sec):

    # costs in dolar
    initial_charge = 3
    tax_per_ride = 0.5
    rate_per_mile = 2 # 40 cents per 1/5 mile
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

def nyc_transit_taxi_shared_costs(date_time_origin, integration_distance, integration_stopped_time, waiting_time_stop,\
shared_distance, shared_stopped_time, transit_destination_first, destinations_distance, destinations_stopped_time):

    # costs in dolar
    initial_charge = 3
    tax_per_ride = 0.5
    rate_per_mile = 2 # 40 cents per 1/5 mile
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

    taxi_passenger_cost += integration_distance * price_per_meter
    taxi_passenger_cost += ((integration_stopped_time/60) * rate_per_minute_stopped)/2

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

def list_best_integrations(df_transit_trips, df_car_trips, dict_transit_taxisharing):

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
    plt.legend(loc=2)
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

list_best_integrations = list_best_integrations(df_transit_trips, df_car_trips, dict_transit_taxisharing)

list_taxi_saving_money = []
list_transit_extra_cost = []
transit_without_sharing = []
for integration in list_best_integrations:
    print integration['transit_trip_id'], integration['car_trip_id']

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

    taxi_individual_cost = nyc_taxi_cost(taxi_date_time_origin, taxi_distance, 0)

    taxi_waiting_time_stop = 0
    if integration['car_arrival_time_transit_stop'] < transit_posisiton['date_time']:
        taxi_waiting_time_stop += (transit_posisiton['date_time'] - integration['car_arrival_time_transit_stop']).total_seconds()

    start_integration_distance = car_posisiton['distance']
    integration_distance = integration['integration_distance']
    shared_distance = integration['shared_distance']
    destinations_distance = integration['destinations_distance']

    transit_destination_first = True
    if integration['car_destination_time'] < integration['transit_destination_time']:
        transit_destination_first = False

    total_distance = start_integration_distance + integration_distance + shared_distance + destinations_distance

    total_integrated_cost = nyc_taxi_cost(taxi_date_time_origin, total_distance, taxi_waiting_time_stop)


    transit_integrated_cost, taxi_integrated_cost = nyc_transit_taxi_shared_costs(taxi_date_time_origin, integration_distance, 0,\
    taxi_waiting_time_stop, shared_distance, 0, transit_destination_first, destinations_distance, 0)

    print 'taxi_individual_cost\t', taxi_individual_cost
    print 'taxi_integrated_cost\t', taxi_integrated_cost

    print '\ntransit_integrated_cost\t', transit_integrated_cost

    print '\ntotal_integrated_cost\t', total_integrated_cost
    print 'transit + taxi\t\t', transit_integrated_cost + taxi_integrated_cost
    print '======================================'
    # break
    taxi_passenger_saving_money = taxi_individual_cost - taxi_integrated_cost
    transit_passenger_cost = transit_integrated_cost

    list_taxi_saving_money.append(taxi_passenger_saving_money)
    list_transit_extra_cost.append(transit_passenger_cost)

plot_cdf_two_curves(list_taxi_saving_money, list_transit_extra_cost, 'taxi saving money', 'transit extra cost', 'dollars', chart_path)
