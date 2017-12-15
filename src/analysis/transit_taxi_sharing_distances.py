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

df_matching_trips = pd.read_csv(matching_trips_path)
df_matching_trips['car_arrival_time_transit_stop'] = pd.to_datetime(df_matching_trips['car_arrival_time_transit_stop'])
df_matching_trips['transit_destination_time'] = pd.to_datetime(df_matching_trips['transit_destination_time'])
df_matching_trips['car_destination_time'] = pd.to_datetime(df_matching_trips['car_destination_time'])

df_transit_trips = pd.read_csv(transit_trips_path)
df_transit_trips['date_time'] = pd.to_datetime(df_transit_trips['date_time'])

print df_transit_trips

df_car_trips = pd.read_csv(car_trips_path)
df_car_trips['date_time'] = pd.to_datetime(df_car_trips['date_time'])

dict_transit_taxisharing = group_df_rows(df_matching_trips, 'transit_trip_id', '')
print len(dict_transit_taxisharing)

list_best_integrations = list_best_integrations(df_transit_trips, df_car_trips, dict_transit_taxisharing)

list_transit_origin_acceptance = []
list_car_origin_acceptance = []
list_car_acceptance_integration = []
list_car_integration_destination = []
list_car_between_destinations = []
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

    # taxi_private_cost = nyc_taxi_cost(taxi_date_time_origin, taxi_distance, 0)

    taxi_waiting_time_stop = 0
    if integration['car_arrival_time_transit_stop'] < transit_posisiton['date_time']:
        taxi_waiting_time_stop += (transit_posisiton['date_time'] - integration['car_arrival_time_transit_stop']).total_seconds()

    list_transit_origin_acceptance.append(transit_posisiton['distance']/1000)
    list_car_origin_acceptance.append(car_posisiton['distance']/1000)
    list_car_acceptance_integration.append(integration['integration_distance']/1000)
    list_car_integration_destination.append(integration['shared_distance']/1000)
    list_car_between_destinations.append(integration['destinations_distance']/1000)

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
#plt.plot(ecdf_transit_origin_acceptance.x, ecdf_transit_origin_acceptance.y, label='transit origin-acceptance')
plt.plot(ecdf_car_origin_acceptance.x, ecdf_car_origin_acceptance.y, label='car origin-acceptance')
plt.plot(ecdf_car_acceptance_integration.x, ecdf_car_acceptance_integration.y, label='car acceptance-integration')
plt.plot(ecdf_car_integration_destination.x, ecdf_car_integration_destination.y, label='car integration-destination')
plt.plot(ecdf_car_between_destinations.x, ecdf_car_between_destinations.y, label='car between-destinations')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
plt.grid()
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('distance (km)')
ax.set_ylabel('CDF')
plt.tight_layout()
fig.savefig(chart_path + 'cdf_distance_segments.png')
