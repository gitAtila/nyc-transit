'''
    Compare segment and factor pricing policies
python max_benefit_segment_proportional.py ~/Documents/Projeto_2020/passenger_trips/all_modes.csv ~/Documents/Projeto_2020/matching/transit_taxi/survey/max_benefit_real_1_05_05_inf.csv ~/Documents/Projeto_2020/matching/transit_taxi/survey/max_benefit_real_prop_inf_05.csv ~/Dropbox/Projeto_2020/resultados/
'''

from sys import argv
import pandas as pd
import numpy as np
import time

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from statsmodels.distributions.empirical_distribution import ECDF
plt.rcParams.update({'font.size': 16})

transit_private_trips_path = argv[1]

max_benefit_seg_path = argv[2]
max_benefit_prop_path = argv[3]

result_path = argv[4]

# colormap = plt.cm.nipy_spectral

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

def taxi_passenger_saving_money(df_max_benefit):
    list_taxi_passenger_saving_money = []
    for index, max_benefit_trip in df_max_benefit.iterrows():
        list_taxi_passenger_saving_money.append((max_benefit_trip['taxi_private_cost']\
        - max_benefit_trip['taxi_shared_cost'])/max_benefit_trip['taxi_private_cost'])

    return list_taxi_passenger_saving_money

def transit_passenger_saving_time(transit_private_trips_path, df_max_benefit):

    list_transit_passenger_bp_saving_time = []

    df_transit_private_trips = pd.read_csv(transit_private_trips_path)
    df_transit_private_trips = df_transit_private_trips[df_transit_private_trips['sampn_perno_tripno']\
    .isin(df_max_benefit['transit_id'].unique())]
    df_transit_private_trips['date_time'] = pd.to_datetime(df_transit_private_trips['date_time'])
    dict_transit_private_trips = group_df_rows(df_transit_private_trips, 'sampn_perno_tripno')

    # df_max_benefit['transit_original_destination_time'] = pd.to_datetime(df_max_benefit['transit_original_destination_time'])
    df_max_benefit['transit_destination_time'] = pd.to_datetime(df_max_benefit['transit_destination_time'])
    df_max_benefit['taxi_destination_time'] = pd.to_datetime(df_max_benefit['taxi_destination_time'])

    for index, max_benefit_trip in df_max_benefit.iterrows():
        # print max_benefit_trip
        transit_origin_time = dict_transit_private_trips[max_benefit_trip['transit_id']][0]['date_time']

        transit_original_duration = (dict_transit_private_trips[max_benefit_trip['transit_id']][-1]['date_time']\
        - transit_origin_time).total_seconds()
        transit_new_duration = (max_benefit_trip['transit_destination_time'] - transit_origin_time).total_seconds()

        transit_passenger_bp_saving_time = (transit_original_duration - transit_new_duration)/transit_original_duration
        list_transit_passenger_bp_saving_time.append(transit_passenger_bp_saving_time)

    return list_transit_passenger_bp_saving_time

df_max_benefit_seg = pd.read_csv(max_benefit_seg_path)
df_max_benefit_prop = pd.read_csv(max_benefit_prop_path)

list_saving_money_seg = taxi_passenger_saving_money(df_max_benefit_seg)
list_saving_money_prop = taxi_passenger_saving_money(df_max_benefit_prop)
list_saving_time_seg = transit_passenger_saving_time(transit_private_trips_path, df_max_benefit_seg)
list_saving_time_prop = transit_passenger_saving_time(transit_private_trips_path, df_max_benefit_prop)

list_saving_money_seg.sort()
list_saving_money_prop.sort()
list_saving_time_seg.sort()
list_saving_time_prop.sort()

'''
    Saving money
'''

ecdf_saving_money_seg = ECDF(list_saving_money_seg)
ecdf_saving_money_prop = ECDF(list_saving_money_prop)

fig, ax = plt.subplots()
# ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_saving_money))])
plt.plot(ecdf_saving_money_seg.x, ecdf_saving_money_seg.y, label='Segment pricing policy')
plt.plot(ecdf_saving_money_prop.x, ecdf_saving_money_prop.y, label='Proportional pricing policy')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('Saving Money (orig - new)/orig')
ax.set_ylabel('CDF')
plt.tight_layout()
fig.savefig(result_path + 'max_benefit_seg_prop_money.pdf')

'''
    Saving time
'''

ecdf_saving_time_seg = ECDF(list_saving_time_seg)
ecdf_saving_time_prop = ECDF(list_saving_time_prop)

fig, ax = plt.subplots()
# ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_saving_time))])
plt.plot(ecdf_saving_time_seg.x, ecdf_saving_time_seg.y, label='Segment pricing policy')
plt.plot(ecdf_saving_time_prop.x, ecdf_saving_time_prop.y, label='Proportional pricing policy')


# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('Saving Time (orig - new)/orig')
ax.set_ylabel('CDF')
plt.tight_layout()
fig.savefig(result_path + 'max_benefit_seg_prop_time.pdf')
