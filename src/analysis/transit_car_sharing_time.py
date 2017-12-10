'''
    Analyse estimatives of cost from transit car matching
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

def saving_extra_time(dict_transit_taxisharing):

    list_saving_time = []
    list_extra_time = []
    for transit_trip_id, list_integrations in dict_transit_taxisharing.iteritems():

        transit_trip = df_transit_trips[df_transit_trips['sampn_perno_tripno'] == transit_trip_id]
        dict_car_taxisharing = group_list_dict(list_integrations, 'car_trip_id')
        print '\n', transit_trip_id, len(dict_car_taxisharing)

        best_car_saving_time = -maxint
        best_car_cost_benefit = {}
        for car_trip_id, list_car_integrations in dict_car_taxisharing.iteritems():
            car_trip = df_car_trips[df_car_trips['sampn_perno_tripno'] == car_trip_id]
            print '\t',car_trip_id, len(list_car_integrations)

            max_saving_time = -maxint
            best_position_cost_benefit = {'transit_saving_time': 0, 'car_extra_time': 0}
            for integration in list_car_integrations:
                transit_posisiton = transit_trip[(transit_trip['trip_sequence'] == integration['transit_trip_sequence'])\
                & (transit_trip['pos_sequence'] == integration['transit_pos_sequence'])]
                car_posisiton = car_trip[(car_trip['trip_sequence'] == integration['car_trip_sequence'])\
                & (car_trip['pos_sequence'] == integration['car_pos_sequence'])]

                transit_saving_time = (transit_trip['date_time'].iloc[-1] - integration['transit_destination_time']).total_seconds()/60
                car_extra_time = (integration['car_destination_time'] - car_trip['date_time'].iloc[-1]).total_seconds()/60

                if transit_saving_time > max_saving_time:
                    max_saving_time = transit_saving_time
                    best_position_cost_benefit['transit_saving_time'] = transit_saving_time
                    best_position_cost_benefit['car_extra_time'] = car_extra_time

            # print '\tmax_saving_time', max_saving_time
            if max_saving_time > best_car_saving_time:
                best_car_saving_time = max_saving_time
                best_car_cost_benefit = best_position_cost_benefit


        print '\ttransit_saving_time\t',best_car_cost_benefit['transit_saving_time']
        print '\tcar_extra_time\t\t',best_car_cost_benefit['car_extra_time']
        list_saving_time.append(best_car_cost_benefit['transit_saving_time'])
        list_extra_time.append(best_car_cost_benefit['car_extra_time'])

    return list_saving_time, list_extra_time

def plot_cdf_two_curves(list_curve_1, list_curve_2, label_curve_1, label_curve_2, x_label, chart_path):
    list_curve_1.sort()
    list_curve_2.sort()

    ecdf_curve_1 = ECDF(list_curve_1)
    ecdf_curve_2 = ECDF(list_curve_2)

    fig, ax = plt.subplots()
    plt.plot(ecdf_curve_1.x, ecdf_curve_1.y, label=label_curve_1)
    plt.plot(ecdf_curve_2.x, ecdf_curve_2.y, label=label_curve_2)

    # ax.xaxis.set_major_locator(ticker.MultipleLocator(30)) # set x sticks interal
    plt.grid()
    plt.legend(loc=4)
    # ax.set_title('Saturday')
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

list_saving_time, list_extra_time = saving_extra_time(dict_transit_taxisharing)

plot_cdf_two_curves(list_saving_time, list_extra_time, 'transit saving time', 'taxi extra time',\
'Time in Minutes', chart_path)
# select best car for each transit trip
