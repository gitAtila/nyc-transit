'''
    Vary cost policies and evaluate matchings
'''

from sys import argv
import pandas as pd
import numpy as np

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

extra_cost_chart_path = argv[10]
extra_money_chart_path = argv[11]
saving_money_chart_path = argv[12]

tp_extra_time_chart_path = argv[13]
td_extra_time_chart_path = argv[14]
saving_time_chart_path = argv[15]

colormap = plt.cm.nipy_spectral

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

def extra_saving_money(df_max_benefit):
    list_transit_passenger_extra_cost = []
    list_taxi_driver_extra_money = []
    list_taxi_passenger_saving_money = []

    for index, max_benefit_trip in df_max_benefit.iterrows():
        list_transit_passenger_extra_cost.append(max_benefit_trip['transit_shared_cost'])
        list_taxi_passenger_saving_money.append(max_benefit_trip['taxi_private_cost'] - max_benefit_trip['taxi_shared_cost'])
        list_taxi_driver_extra_money.append(max_benefit_trip['transit_shared_cost'] + max_benefit_trip['taxi_shared_cost']\
        - max_benefit_trip['taxi_private_cost'])

    return list_transit_passenger_extra_cost, list_taxi_driver_extra_money, list_taxi_passenger_saving_money

def extra_saving_time(taxi_private_trips_path, df_max_benefit):

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
        transit_passenger_bp_saving_time = (max_benefit_trip['transit_original_destination_time']\
        - max_benefit_trip['transit_destination_time']).total_seconds()/60
        list_transit_passenger_bp_saving_time.append(transit_passenger_bp_saving_time)

        taxi_private_destination_time = dict_taxi_private_trips[max_benefit_trip['taxi_id']][-1]['date_time']
        taxi_passenger_extra_time = (max_benefit_trip['taxi_destination_time']\
        - taxi_private_destination_time).total_seconds()/60
        list_taxi_passenger_extra_time.append(taxi_passenger_extra_time)

        last_destination_time = max_benefit_trip['transit_destination_time']
        if max_benefit_trip['taxi_destination_time'] > last_destination_time:
            last_destination_time = max_benefit_trip['taxi_destination_time']
        taxi_driver_extra_time = (last_destination_time - taxi_private_destination_time).total_seconds()/60
        list_taxi_driver_extra_time.append(taxi_driver_extra_time)

    return list_taxi_passenger_extra_time, list_taxi_driver_extra_time, list_transit_passenger_bp_saving_time

list_df_max_benefit = []
list_df_max_benefit.append(pd.read_csv(max_benefit_05_05_05_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_1_05_05_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_05_1_05_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_05_05_1_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_1_1_05_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_1_05_1_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_05_1_1_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_1_1_1_path))

list_extra_saving_money = []
list_extra_saving_time = []
for df_max_benefit in list_df_max_benefit:
    list_extra_saving_money.append(extra_saving_money(df_max_benefit))
    list_extra_saving_time.append(extra_saving_time(taxi_private_trips_path, df_max_benefit))

for index in range(len(list_extra_saving_money)):
    list_extra_saving_money[index][0].sort()
    list_extra_saving_money[index][1].sort()
    list_extra_saving_money[index][2].sort()

    list_extra_saving_time[index][0].sort()
    list_extra_saving_time[index][1].sort()
    list_extra_saving_time[index][2].sort()
'''
    Extra costs
'''
# print list_extra_saving_money[0][0]

ecdf_extra_cost_05_05_05 = ECDF(list_extra_saving_money[0][0])
ecdf_extra_cost_1_05_05 = ECDF(list_extra_saving_money[1][0])
ecdf_extra_cost_05_1_05 = ECDF(list_extra_saving_money[2][0])
ecdf_extra_cost_05_05_1 = ECDF(list_extra_saving_money[3][0])
ecdf_extra_cost_1_1_05 = ECDF(list_extra_saving_money[4][0])
ecdf_extra_cost_1_05_1 = ECDF(list_extra_saving_money[5][0])
ecdf_extra_cost_05_1_1 = ECDF(list_extra_saving_money[6][0])
ecdf_extra_cost_1_1_1 = ECDF(list_extra_saving_money[7][0])

fig, ax = plt.subplots()
ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_extra_saving_money))])
plt.plot(ecdf_extra_cost_05_05_05.x, ecdf_extra_cost_05_05_05.y, label='a=0.5 b=0.5 c=0.5')
plt.plot(ecdf_extra_cost_1_05_05.x, ecdf_extra_cost_1_05_05.y, label='a=1.0 b=0.5 c=0.5')
plt.plot(ecdf_extra_cost_05_1_05.x, ecdf_extra_cost_05_1_05.y, label='a=0.5 b=1.0 c=0.5')
plt.plot(ecdf_extra_cost_05_05_1.x, ecdf_extra_cost_05_05_1.y, label='a=0.5 b=0.5 c=1.0')
plt.plot(ecdf_extra_cost_1_1_05.x, ecdf_extra_cost_1_1_05.y, label='a=1.0 b=1.0 c=0.5')
plt.plot(ecdf_extra_cost_1_05_1.x, ecdf_extra_cost_1_05_1.y, label='a=1.0 b=0.5 c=1.0')
plt.plot(ecdf_extra_cost_05_1_1.x, ecdf_extra_cost_05_1_1.y, label='a=0.5 b=1.0 c=1.0')
plt.plot(ecdf_extra_cost_1_1_1.x, ecdf_extra_cost_1_1_1.y, label='a=1.0 b=1.0 c=1.0')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
plt.grid()
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('transit passenger sharing cost (dollars)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(extra_cost_chart_path)

'''
    Extra money
'''

ecdf_extra_money_05_05_05 = ECDF(list_extra_saving_money[0][1])
ecdf_extra_money_1_05_05 = ECDF(list_extra_saving_money[1][1])
ecdf_extra_money_05_1_05 = ECDF(list_extra_saving_money[2][1])
ecdf_extra_money_05_05_1 = ECDF(list_extra_saving_money[3][1])
ecdf_extra_money_1_1_05 = ECDF(list_extra_saving_money[4][1])
ecdf_extra_money_1_05_1 = ECDF(list_extra_saving_money[5][1])
ecdf_extra_money_05_1_1 = ECDF(list_extra_saving_money[6][1])
ecdf_extra_money_1_1_1 = ECDF(list_extra_saving_money[7][1])

fig, ax = plt.subplots()
ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_extra_saving_money))])
plt.plot(ecdf_extra_money_05_05_05.x, ecdf_extra_money_05_05_05.y, label='a=0.5 b=0.5 c=0.5')
plt.plot(ecdf_extra_money_1_05_05.x, ecdf_extra_money_1_05_05.y, label='a=1.0 b=0.5 c=0.5')
plt.plot(ecdf_extra_money_05_1_05.x, ecdf_extra_money_05_1_05.y, label='a=0.5 b=1.0 c=0.5')
plt.plot(ecdf_extra_money_05_05_1.x, ecdf_extra_money_05_05_1.y, label='a=0.5 b=0.5 c=1.0')
plt.plot(ecdf_extra_money_1_1_05.x, ecdf_extra_money_1_1_05.y, label='a=1.0 b=1.0 c=0.5')
plt.plot(ecdf_extra_money_1_05_1.x, ecdf_extra_money_1_05_1.y, label='a=1.0 b=0.5 c=1.0')
plt.plot(ecdf_extra_money_05_1_1.x, ecdf_extra_money_05_1_1.y, label='a=0.5 b=1.0 c=1.0')
plt.plot(ecdf_extra_money_1_1_1.x, ecdf_extra_money_1_1_1.y, label='a=1.0 b=1.0 c=1.0')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
plt.grid()
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('taxi driver extra money (dollars)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(extra_money_chart_path)

'''
    Saving money
'''

ecdf_saving_money_05_05_05 = ECDF(list_extra_saving_money[0][2])
ecdf_saving_money_1_05_05 = ECDF(list_extra_saving_money[1][2])
ecdf_saving_money_05_1_05 = ECDF(list_extra_saving_money[2][2])
ecdf_saving_money_05_05_1 = ECDF(list_extra_saving_money[3][2])
ecdf_saving_money_1_1_05 = ECDF(list_extra_saving_money[4][2])
ecdf_saving_money_1_05_1 = ECDF(list_extra_saving_money[5][2])
ecdf_saving_money_05_1_1 = ECDF(list_extra_saving_money[6][2])
ecdf_saving_money_1_1_1 = ECDF(list_extra_saving_money[7][2])

fig, ax = plt.subplots()
ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_extra_saving_money))])
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
ax.set_xlabel('taxi passenger saving money (dollars)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(saving_money_chart_path)

'''
    Extra time
'''

ecdf_extra_time_05_05_05 = ECDF(list_extra_saving_time[0][0])
ecdf_extra_time_1_05_05 = ECDF(list_extra_saving_time[1][0])
ecdf_extra_time_05_1_05 = ECDF(list_extra_saving_time[2][0])
ecdf_extra_time_05_05_1 = ECDF(list_extra_saving_time[3][0])
ecdf_extra_time_1_1_05 = ECDF(list_extra_saving_time[4][0])
ecdf_extra_time_1_05_1 = ECDF(list_extra_saving_time[5][0])
ecdf_extra_time_05_1_1 = ECDF(list_extra_saving_time[6][0])
ecdf_extra_time_1_1_1 = ECDF(list_extra_saving_time[7][0])

fig, ax = plt.subplots()
ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_extra_saving_time))])
plt.plot(ecdf_extra_time_05_05_05.x, ecdf_extra_time_05_05_05.y, label='a=0.5 b=0.5 c=0.5')
plt.plot(ecdf_extra_time_1_05_05.x, ecdf_extra_time_1_05_05.y, label='a=1.0 b=0.5 c=0.5')
plt.plot(ecdf_extra_time_05_1_05.x, ecdf_extra_time_05_1_05.y, label='a=0.5 b=1.0 c=0.5')
plt.plot(ecdf_extra_time_05_05_1.x, ecdf_extra_time_05_05_1.y, label='a=0.5 b=0.5 c=1.0')
plt.plot(ecdf_extra_time_1_1_05.x, ecdf_extra_time_1_1_05.y, label='a=1.0 b=1.0 c=0.5')
plt.plot(ecdf_extra_time_1_05_1.x, ecdf_extra_time_1_05_1.y, label='a=1.0 b=0.5 c=1.0')
plt.plot(ecdf_extra_time_05_1_1.x, ecdf_extra_time_05_1_1.y, label='a=0.5 b=1.0 c=1.0')
plt.plot(ecdf_extra_time_1_1_1.x, ecdf_extra_time_1_1_1.y, label='a=1.0 b=1.0 c=1.0')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
plt.grid()
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('taxi passenger extra time (minutes)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(tp_extra_time_chart_path)

'''
    Extra time
'''

ecdf_extra_time_05_05_05 = ECDF(list_extra_saving_time[0][1])
ecdf_extra_time_1_05_05 = ECDF(list_extra_saving_time[1][1])
ecdf_extra_time_05_1_05 = ECDF(list_extra_saving_time[2][1])
ecdf_extra_time_05_05_1 = ECDF(list_extra_saving_time[3][1])
ecdf_extra_time_1_1_05 = ECDF(list_extra_saving_time[4][1])
ecdf_extra_time_1_05_1 = ECDF(list_extra_saving_time[5][1])
ecdf_extra_time_05_1_1 = ECDF(list_extra_saving_time[6][1])
ecdf_extra_time_1_1_1 = ECDF(list_extra_saving_time[7][1])

fig, ax = plt.subplots()
ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_extra_saving_time))])
plt.plot(ecdf_extra_time_05_05_05.x, ecdf_extra_time_05_05_05.y, label='a=0.5 b=0.5 c=0.5')
plt.plot(ecdf_extra_time_1_05_05.x, ecdf_extra_time_1_05_05.y, label='a=1.0 b=0.5 c=0.5')
plt.plot(ecdf_extra_time_05_1_05.x, ecdf_extra_time_05_1_05.y, label='a=0.5 b=1.0 c=0.5')
plt.plot(ecdf_extra_time_05_05_1.x, ecdf_extra_time_05_05_1.y, label='a=0.5 b=0.5 c=1.0')
plt.plot(ecdf_extra_time_1_1_05.x, ecdf_extra_time_1_1_05.y, label='a=1.0 b=1.0 c=0.5')
plt.plot(ecdf_extra_time_1_05_1.x, ecdf_extra_time_1_05_1.y, label='a=1.0 b=0.5 c=1.0')
plt.plot(ecdf_extra_time_05_1_1.x, ecdf_extra_time_05_1_1.y, label='a=0.5 b=1.0 c=1.0')
plt.plot(ecdf_extra_time_1_1_1.x, ecdf_extra_time_1_1_1.y, label='a=1.0 b=1.0 c=1.0')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
plt.grid()
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('taxi driver extra time (minutes)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(td_extra_time_chart_path)

'''
    Saving time
'''

ecdf_saving_time_05_05_05 = ECDF(list_extra_saving_time[0][2])
ecdf_saving_time_1_05_05 = ECDF(list_extra_saving_time[1][2])
ecdf_saving_time_05_1_05 = ECDF(list_extra_saving_time[2][2])
ecdf_saving_time_05_05_1 = ECDF(list_extra_saving_time[3][2])
ecdf_saving_time_1_1_05 = ECDF(list_extra_saving_time[4][2])
ecdf_saving_time_1_05_1 = ECDF(list_extra_saving_time[5][2])
ecdf_saving_time_05_1_1 = ECDF(list_extra_saving_time[6][2])
ecdf_saving_time_1_1_1 = ECDF(list_extra_saving_time[7][2])

fig, ax = plt.subplots()
ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_extra_saving_time))])
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
ax.set_xlabel('transit passenger saving time (minutes)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(saving_time_chart_path)
