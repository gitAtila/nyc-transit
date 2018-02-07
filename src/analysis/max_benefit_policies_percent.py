'''
    Vary cost policies and evaluate matchings
'''

from sys import argv
import pandas as pd
import numpy as np
import time

import matplotlib.pyplot as plt
from statsmodels.distributions.empirical_distribution import ECDF

taxi_private_trips_path = argv[1]

max_benefit_05_05_05_path = argv[2]
max_benefit_1_05_05_path = argv[3]
max_benefit_05_1_05_path = argv[4]
max_benefit_05_05_1_path = argv[5]
max_benefit_1_1_05_path = argv[6]
max_benefit_1_05_1_path = argv[7]
max_benefit_05_1_1_path = argv[8]
max_benefit_1_1_1_path = argv[9]

saving_money_chart_path = argv[10]
saving_time_chart_path = argv[11]

colormap = plt.cm.nipy_spectral

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

def transit_passenger_saving_time(taxi_private_trips_path, df_max_benefit):

    list_transit_passenger_bp_saving_time = []
    list_taxi_passenger_extra_time = []
    list_taxi_driver_extra_time = []

    df_taxi_private_trips = pd.read_csv(taxi_private_trips_path)
    df_taxi_private_trips = df_taxi_private_trips[df_taxi_private_trips['sampn_perno_tripno']\
    .isin(df_max_benefit['taxi_id'].unique())]
    df_taxi_private_trips['date_time'] = pd.to_datetime(df_taxi_private_trips['date_time'])
    dict_taxi_private_trips = group_df_rows(df_taxi_private_trips, 'sampn_perno_tripno')

    df_max_benefit['transit_original_destination_time'] = pd.to_datetime(df_max_benefit['transit_original_destination_time'])
    df_max_benefit['transit_destination_time'] = pd.to_datetime(df_max_benefit['transit_destination_time'])
    df_max_benefit['taxi_destination_time'] = pd.to_datetime(df_max_benefit['taxi_destination_time'])

    for index, max_benefit_trip in df_max_benefit.iterrows():
        transit_passenger_bp_saving_time = (time.mktime(max_benefit_trip['transit_original_destination_time'].timetuple())\
        - time.mktime(max_benefit_trip['transit_destination_time'].timetuple()))\
        /time.mktime(max_benefit_trip['transit_original_destination_time'].timetuple())
        list_transit_passenger_bp_saving_time.append(transit_passenger_bp_saving_time)

    return list_transit_passenger_bp_saving_time

list_df_max_benefit = []
list_df_max_benefit.append(pd.read_csv(max_benefit_05_05_05_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_1_05_05_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_05_1_05_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_05_05_1_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_1_1_05_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_1_05_1_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_05_1_1_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_1_1_1_path))

list_saving_money = []
list_saving_time = []
for df_max_benefit in list_df_max_benefit:
    list_saving_money.append(taxi_passenger_saving_money(df_max_benefit))
    list_saving_time.append(transit_passenger_saving_time(taxi_private_trips_path, df_max_benefit))

for index in range(len(list_saving_money)):
    list_saving_money[index].sort()
    list_saving_time[index].sort()

'''
    Saving money
'''

ecdf_saving_money_05_05_05 = ECDF(list_saving_money[0])
ecdf_saving_money_1_05_05 = ECDF(list_saving_money[1])
ecdf_saving_money_05_1_05 = ECDF(list_saving_money[2])
ecdf_saving_money_05_05_1 = ECDF(list_saving_money[3])
ecdf_saving_money_1_1_05 = ECDF(list_saving_money[4])
ecdf_saving_money_1_05_1 = ECDF(list_saving_money[5])
ecdf_saving_money_05_1_1 = ECDF(list_saving_money[6])
ecdf_saving_money_1_1_1 = ECDF(list_saving_money[7])

fig, ax = plt.subplots()
ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_saving_money))])
plt.plot(ecdf_saving_money_05_05_05.x, ecdf_saving_money_05_05_05.y, label='a=0.5 b=0.5 c=0.5')
plt.plot(ecdf_saving_money_1_05_05.x, ecdf_saving_money_1_05_05.y, label='a=1.0 b=0.5 c=0.5')
plt.plot(ecdf_saving_money_05_1_05.x, ecdf_saving_money_05_1_05.y, label='a=0.5 b=1.0 c=0.5')
plt.plot(ecdf_saving_money_05_05_1.x, ecdf_saving_money_05_05_1.y, label='a=0.5 b=0.5 c=1.0')
plt.plot(ecdf_saving_money_1_1_05.x, ecdf_saving_money_1_1_05.y, label='a=1.0 b=1.0 c=0.5')
plt.plot(ecdf_saving_money_1_05_1.x, ecdf_saving_money_1_05_1.y, label='a=1.0 b=0.5 c=1.0')
plt.plot(ecdf_saving_money_05_1_1.x, ecdf_saving_money_05_1_1.y, label='a=0.5 b=1.0 c=1.0')
plt.plot(ecdf_saving_money_1_1_1.x, ecdf_saving_money_1_1_1.y, label='a=1.0 b=1.0 c=1.0')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
plt.grid()
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('taxi saving money (orig - new)/orig')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(saving_money_chart_path)

'''
    Saving time
'''

ecdf_saving_time_05_05_05 = ECDF(list_saving_time[0])
ecdf_saving_time_1_05_05 = ECDF(list_saving_time[1])
ecdf_saving_time_05_1_05 = ECDF(list_saving_time[2])
ecdf_saving_time_05_05_1 = ECDF(list_saving_time[3])
ecdf_saving_time_1_1_05 = ECDF(list_saving_time[4])
ecdf_saving_time_1_05_1 = ECDF(list_saving_time[5])
ecdf_saving_time_05_1_1 = ECDF(list_saving_time[6])
ecdf_saving_time_1_1_1 = ECDF(list_saving_time[7])

fig, ax = plt.subplots()
ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_saving_time))])
plt.plot(ecdf_saving_time_05_05_05.x, ecdf_saving_time_05_05_05.y, label='a=0.5 b=0.5 c=0.5')
plt.plot(ecdf_saving_time_1_05_05.x, ecdf_saving_time_1_05_05.y, label='a=1.0 b=0.5 c=0.5')
plt.plot(ecdf_saving_time_05_1_05.x, ecdf_saving_time_05_1_05.y, label='a=0.5 b=1.0 c=0.5')
plt.plot(ecdf_saving_time_05_05_1.x, ecdf_saving_time_05_05_1.y, label='a=0.5 b=0.5 c=1.0')
plt.plot(ecdf_saving_time_1_1_05.x, ecdf_saving_time_1_1_05.y, label='a=1.0 b=1.0 c=0.5')
plt.plot(ecdf_saving_time_1_05_1.x, ecdf_saving_time_1_05_1.y, label='a=1.0 b=0.5 c=1.0')
plt.plot(ecdf_saving_time_05_1_1.x, ecdf_saving_time_05_1_1.y, label='a=0.5 b=1.0 c=1.0')
plt.plot(ecdf_saving_time_1_1_1.x, ecdf_saving_time_1_1_1.y, label='a=1.0 b=1.0 c=1.0')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
plt.grid()
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('transit saving time (orig - new)/orig')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(saving_time_chart_path)
