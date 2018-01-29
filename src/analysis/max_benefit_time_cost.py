'''
    Read results provided by transit_taxi_max_benefit and analyse them
'''

from sys import argv
import pandas as pd

import matplotlib.pyplot as plt
from statsmodels.distributions.empirical_distribution import ECDF

max_benefit_trips_path = argv[1]
taxi_private_trips_path = argv[2]
times_chart_path = argv[3]
money_chart_path = argv[4]

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

df_max_benefit_trip = pd.read_csv(max_benefit_trips_path)
df_max_benefit_trip['transit_original_destination_time'] = pd.to_datetime(df_max_benefit_trip['transit_original_destination_time'])
df_max_benefit_trip['transit_destination_time'] = pd.to_datetime(df_max_benefit_trip['transit_destination_time'])
df_max_benefit_trip['taxi_destination_time'] = pd.to_datetime(df_max_benefit_trip['taxi_destination_time'])
# print df_max_benefit_trip

# read taxi private route
df_taxi_private_trips = pd.read_csv(taxi_private_trips_path)
df_taxi_private_trips = df_taxi_private_trips[df_taxi_private_trips['sampn_perno_tripno']\
.isin(df_max_benefit_trip['taxi_id'].unique())]
df_taxi_private_trips['date_time'] = pd.to_datetime(df_taxi_private_trips['date_time'])
dict_taxi_private_trip = group_df_rows(df_taxi_private_trips, 'sampn_perno_tripno')

# how much time did transit passengers save?
# how much time did taxi passenger expend more?

# how much money did transit passengers pay more?
# how much money did taxi passengers save?

list_transit_passenger_saving_time = []
list_taxi_passenger_extra_time = []

list_transit_passenger_extra_cost = []
list_taxi_passenger_saving_money = []

for index, max_benefit_trip in df_max_benefit_trip.iterrows():
    transit_passenger_saving_time = (max_benefit_trip['transit_original_destination_time']\
    - max_benefit_trip['transit_destination_time']).total_seconds()/60
    list_transit_passenger_saving_time.append(transit_passenger_saving_time)

    taxi_private_destination_time = dict_taxi_private_trip[max_benefit_trip['taxi_id']][-1]['date_time']
    taxi_passenger_extra_time = (max_benefit_trip['taxi_destination_time']\
    - taxi_private_destination_time).total_seconds()/60
    list_taxi_passenger_extra_time.append(taxi_passenger_extra_time)

    list_transit_passenger_extra_cost.append(max_benefit_trip['transit_shared_cost'])
    list_taxi_passenger_saving_money.append(max_benefit_trip['taxi_private_cost'] - max_benefit_trip['taxi_shared_cost'])

plot_cdf_two_curves(list_transit_passenger_saving_time, list_taxi_passenger_extra_time,\
'transit passenger saving time', 'taxi passenger extra time', 'difference of time (minutes)',\
times_chart_path)

plot_cdf_two_curves(list_transit_passenger_extra_cost, list_taxi_passenger_saving_money,\
'transit passenger sharing cost', 'taxi passenger saving money', 'difference of money (dollars)',\
money_chart_path)
