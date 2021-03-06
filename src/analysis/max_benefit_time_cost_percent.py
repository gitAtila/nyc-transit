'''
    Read results provided by transit_taxi_max_benefit and analyse them
'''

from sys import argv
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 16})

from statsmodels.distributions.empirical_distribution import ECDF

taxi_private_trips_path = argv[1]
transit_private_trips_path = argv[2]

max_benefit_trips_path = argv[3]

# times_chart_path = argv[4]
# money_chart_path = argv[5]

transit_passenger_chart_path = argv[4]
taxi_passenger_chart_path = argv[5]

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

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

def scatter_plot(list_x_values, list_y_values, x_label, y_label, chart_path):

    fig, ax = plt.subplots()
    plt.plot(list_x_values, list_y_values, 'o')

    # ax.set_title('saturday')
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)

    plt.tight_layout()
    fig.savefig(chart_path)

df_max_benefit_trip = pd.read_csv(max_benefit_trips_path)
# df_max_benefit_trip['transit_original_destination_time'] = pd.to_datetime(df_max_benefit_trip['transit_original_destination_time'])
df_max_benefit_trip['transit_destination_time'] = pd.to_datetime(df_max_benefit_trip['transit_destination_time'])
df_max_benefit_trip['taxi_destination_time'] = pd.to_datetime(df_max_benefit_trip['taxi_destination_time'])
# print df_max_benefit_trip

# read taxi private route
df_taxi_private_trips = pd.read_csv(taxi_private_trips_path)
df_taxi_private_trips = df_taxi_private_trips[df_taxi_private_trips['sampn_perno_tripno']\
.isin(df_max_benefit_trip['taxi_id'].unique())]
df_taxi_private_trips['date_time'] = pd.to_datetime(df_taxi_private_trips['date_time'])
dict_taxi_private_trip = group_df_rows(df_taxi_private_trips, 'sampn_perno_tripno')

df_transit_private_trips = pd.read_csv(transit_private_trips_path)
df_transit_private_trips = df_transit_private_trips[df_transit_private_trips['sampn_perno_tripno']\
.isin(df_max_benefit_trip['transit_id'].unique())]
df_transit_private_trips['date_time'] = pd.to_datetime(df_transit_private_trips['date_time'])
dict_transit_private_trip = group_df_rows(df_transit_private_trips, 'sampn_perno_tripno')

# how much time did transit passengers save?
# how much time did taxi passenger expend more?

# how much money did transit passengers pay more?
# how much money did taxi passengers save?

list_transit_passenger_saving_time = []
list_taxi_passenger_extra_time = []

list_transit_passenger_extra_cost = []
list_taxi_passenger_saving_money = []

for index, max_benefit_trip in df_max_benefit_trip.iterrows():

    # transit passenger saving time
    transit_passenger_original_duration = (dict_transit_private_trip[max_benefit_trip['transit_id']][-1]['date_time']\
    - dict_transit_private_trip[max_benefit_trip['transit_id']][0]['date_time']).total_seconds()

    transit_passenger_new_duration = (max_benefit_trip['transit_destination_time']\
    - dict_transit_private_trip[max_benefit_trip['transit_id']][0]['date_time']).total_seconds()

    transit_passenger_saving_time = (transit_passenger_original_duration\
    - transit_passenger_new_duration)/60 #transit_passenger_original_duration
    list_transit_passenger_saving_time.append(transit_passenger_saving_time)

    # taxi passenger extra time
    taxi_passenger_original_duration = (dict_taxi_private_trip[max_benefit_trip['taxi_id']][-1]['date_time']\
    - dict_taxi_private_trip[max_benefit_trip['taxi_id']][0]['date_time']).total_seconds()

    taxi_passenger_new_duration = (max_benefit_trip['taxi_destination_time']\
    - dict_taxi_private_trip[max_benefit_trip['taxi_id']][0]['date_time']).total_seconds()

    taxi_passenger_extra_time = (taxi_passenger_new_duration - taxi_passenger_original_duration)/60
    list_taxi_passenger_extra_time.append(taxi_passenger_extra_time)

    # transit passenger extra cost
    list_transit_passenger_extra_cost.append(max_benefit_trip['transit_shared_cost'])

    # taxi passenger saving money
    taxi_passenger_saving_money = (max_benefit_trip['taxi_private_cost']\
    - max_benefit_trip['taxi_shared_cost'])#/max_benefit_trip['taxi_private_cost']
    list_taxi_passenger_saving_money.append(taxi_passenger_saving_money)

# plot_cdf_two_curves(list_transit_passenger_saving_time, list_taxi_passenger_extra_time,\
# 'transit passenger saving time (minutes)', 'taxi passenger extra time', 'difference of time (minutes)',\
# times_chart_path)
#
# plot_cdf_two_curves(list_transit_passenger_extra_cost, list_taxi_passenger_saving_money,\
# 'transit passenger sharing cost', 'taxi passenger saving money (dollars)', 'difference of money (dollars)',\
# money_chart_path)

scatter_plot(list_transit_passenger_extra_cost, list_transit_passenger_saving_time,\
'Custo Extra (dolares)', 'Economia de Tempo (minutos)', transit_passenger_chart_path)
# print np.corrcoef(list_transit_passenger_extra_cost, list_transit_passenger_saving_time)

scatter_plot(list_taxi_passenger_extra_time, list_taxi_passenger_saving_money, \
'Tempo Extra (minutos)', 'Economia de Dinheiro (dolares)', taxi_passenger_chart_path)
# print np.corrcoef(list_taxi_passenger_saving_money, list_taxi_passenger_extra_time)
