'''
    Vary cost policies and evaluate matchings
'''

from sys import argv
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
from statsmodels.distributions.empirical_distribution import ECDF

taxi_private_trips_path = argv[1]
transit_private_trips_path = argv[2]

max_benefit_05_05_05_path = argv[3]
max_benefit_1_05_05_path = argv[4]
max_benefit_05_1_05_path = argv[5]
max_benefit_05_05_1_path = argv[6]
max_benefit_1_1_05_path = argv[7]
max_benefit_1_05_1_path = argv[8]
max_benefit_05_1_1_path = argv[9]
max_benefit_1_1_1_path = argv[10]

transit_passenger_sharing_cost_path = argv[11]
# taxi_driver_sharing_revenue_path = argv[12]
# taxi_passenger_sharing_cost_path = argv[13]
#
# taxi_passenger_sharing_duration_path = argv[14]
# taxi_driver_sharing_duration_path = argv[15]
# transit_passenger_sharing_duration_path = argv[16]

colormap = plt.cm.nipy_spectral

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

def users_costs(df_max_benefit):
    list_transit_passenger = []
    list_taxi_passenger = []
    list_taxi_driver = []

    for index, max_benefit_trip in df_max_benefit.iterrows():
        list_transit_passenger.append(max_benefit_trip['transit_shared_cost'])
        list_taxi_passenger.append(max_benefit_trip['taxi_shared_cost'])
        list_taxi_driver.append(max_benefit_trip['transit_shared_cost'] + max_benefit_trip['taxi_shared_cost'])

    return list_transit_passenger, list_taxi_driver, list_taxi_passenger

def sharing_duration(taxi_private_trips_path, transit_private_trips_path, df_max_benefit):

    list_transit_passenger_sharing_duration = []
    list_taxi_passenger_sharing_duration = []
    list_taxi_driver_sharing_duration = []

    df_taxi_private_trips = pd.read_csv(taxi_private_trips_path)
    df_transit_private_trips = pd.read_csv(transit_private_trips_path)

    df_taxi_private_trips = df_taxi_private_trips[df_taxi_private_trips['sampn_perno_tripno']\
    .isin(df_max_benefit['taxi_id'].unique())]
    df_transit_private_trips = df_transit_private_trips[df_transit_private_trips['sampn_perno_tripno']\
    .isin(df_max_benefit['transit_id'].unique())]

    df_taxi_private_trips['date_time'] = pd.to_datetime(df_taxi_private_trips['date_time'])
    df_transit_private_trips['date_time'] = pd.to_datetime(df_transit_private_trips['date_time'])

    dict_taxi_private_trips = group_df_rows(df_taxi_private_trips, 'sampn_perno_tripno')
    dict_transit_private_trips = group_df_rows(df_transit_private_trips, 'sampn_perno_tripno')

    print df_max_benefit.iloc[0]

    df_max_benefit['transit_original_destination_time'] = pd.to_datetime(df_max_benefit['transit_original_destination_time'])
    df_max_benefit['transit_destination_time'] = pd.to_datetime(df_max_benefit['transit_destination_time'])
    df_max_benefit['taxi_destination_time'] = pd.to_datetime(df_max_benefit['taxi_destination_time'])

    for index, max_benefit_trip in df_max_benefit.iterrows():
        transit_private_origin_time = dict_transit_private_trips[max_benefit_trip['transit_id']][0]['date_time']
        transit_passenger_sharing_duration = (max_benefit_trip['transit_destination_time'] - transit_private_origin_time).total_seconds()/60
        list_transit_passenger_sharing_duration.append(transit_passenger_sharing_duration)

        taxi_private_origin_time = dict_taxi_private_trips[max_benefit_trip['taxi_id']][0]['date_time']
        taxi_passenger_sharing_duration = (max_benefit_trip['taxi_destination_time']\
        - taxi_private_origin_time).total_seconds()/60
        list_taxi_passenger_sharing_duration.append(taxi_passenger_sharing_duration)

        last_destination_time = max_benefit_trip['transit_destination_time']
        if max_benefit_trip['taxi_destination_time'] > last_destination_time:
            last_destination_time = max_benefit_trip['taxi_destination_time']
        taxi_driver_sharing_duration = (last_destination_time - taxi_private_origin_time).total_seconds()/60
        list_taxi_driver_sharing_duration.append(taxi_driver_sharing_duration)

    return list_taxi_passenger_sharing_duration, list_taxi_driver_sharing_duration, list_transit_passenger_sharing_duration

list_df_max_benefit = []
list_df_max_benefit.append(pd.read_csv(max_benefit_05_05_05_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_1_05_05_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_05_1_05_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_05_05_1_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_1_1_05_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_1_05_1_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_05_1_1_path))
list_df_max_benefit.append(pd.read_csv(max_benefit_1_1_1_path))

list_costs = []
list_sharing_duration = []
for df_max_benefit in list_df_max_benefit:
    list_costs.append(users_costs(df_max_benefit))
    list_sharing_duration.append(sharing_duration(taxi_private_trips_path,\
    transit_private_trips_path, df_max_benefit))

for index in range(len(list_costs)):
    list_costs[index][0].sort()
    list_costs[index][1].sort()
    list_costs[index][2].sort()

    list_sharing_duration[index][0].sort()
    list_sharing_duration[index][1].sort()
    list_sharing_duration[index][2].sort()
'''
    Extra costs
'''
# print list_costs[0][0]

ecdf_extra_cost_05_05_05 = ECDF(list_costs[0][0])
ecdf_extra_cost_1_05_05 = ECDF(list_costs[1][0])
ecdf_extra_cost_05_1_05 = ECDF(list_costs[2][0])
ecdf_extra_cost_05_05_1 = ECDF(list_costs[3][0])
ecdf_extra_cost_1_1_05 = ECDF(list_costs[4][0])
ecdf_extra_cost_1_05_1 = ECDF(list_costs[5][0])
ecdf_extra_cost_05_1_1 = ECDF(list_costs[6][0])
ecdf_extra_cost_1_1_1 = ECDF(list_costs[7][0])

fig, ax = plt.subplots()
ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_costs))])
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
fig.savefig(transit_passenger_sharing_cost_path)

'''
    Extra money
'''

ecdf_extra_money_05_05_05 = ECDF(list_costs[0][1])
ecdf_extra_money_1_05_05 = ECDF(list_costs[1][1])
ecdf_extra_money_05_1_05 = ECDF(list_costs[2][1])
ecdf_extra_money_05_05_1 = ECDF(list_costs[3][1])
ecdf_extra_money_1_1_05 = ECDF(list_costs[4][1])
ecdf_extra_money_1_05_1 = ECDF(list_costs[5][1])
ecdf_extra_money_05_1_1 = ECDF(list_costs[6][1])
ecdf_extra_money_1_1_1 = ECDF(list_costs[7][1])

fig, ax = plt.subplots()
ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_costs))])
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
ax.set_xlabel('taxi driver sharing revenue (dollars)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(taxi_driver_sharing_revenue_path)

'''
    Saving money
'''

ecdf_saving_money_05_05_05 = ECDF(list_costs[0][2])
ecdf_saving_money_1_05_05 = ECDF(list_costs[1][2])
ecdf_saving_money_05_1_05 = ECDF(list_costs[2][2])
ecdf_saving_money_05_05_1 = ECDF(list_costs[3][2])
ecdf_saving_money_1_1_05 = ECDF(list_costs[4][2])
ecdf_saving_money_1_05_1 = ECDF(list_costs[5][2])
ecdf_saving_money_05_1_1 = ECDF(list_costs[6][2])
ecdf_saving_money_1_1_1 = ECDF(list_costs[7][2])

fig, ax = plt.subplots()
ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_costs))])
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
ax.set_xlabel('taxi passenger sharing cost (dollars)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(taxi_passenger_sharing_cost_path)

'''
    Extra time
'''

ecdf_extra_time_05_05_05 = ECDF(list_sharing_duration[0][0])
ecdf_extra_time_1_05_05 = ECDF(list_sharing_duration[1][0])
ecdf_extra_time_05_1_05 = ECDF(list_sharing_duration[2][0])
ecdf_extra_time_05_05_1 = ECDF(list_sharing_duration[3][0])
ecdf_extra_time_1_1_05 = ECDF(list_sharing_duration[4][0])
ecdf_extra_time_1_05_1 = ECDF(list_sharing_duration[5][0])
ecdf_extra_time_05_1_1 = ECDF(list_sharing_duration[6][0])
ecdf_extra_time_1_1_1 = ECDF(list_sharing_duration[7][0])

fig, ax = plt.subplots()
ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_sharing_duration))])
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
ax.set_xlabel('taxi passenger trip sharing duration (minutes)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(taxi_passenger_sharing_duration_path)

'''
    Extra time
'''

ecdf_extra_time_05_05_05 = ECDF(list_sharing_duration[0][1])
ecdf_extra_time_1_05_05 = ECDF(list_sharing_duration[1][1])
ecdf_extra_time_05_1_05 = ECDF(list_sharing_duration[2][1])
ecdf_extra_time_05_05_1 = ECDF(list_sharing_duration[3][1])
ecdf_extra_time_1_1_05 = ECDF(list_sharing_duration[4][1])
ecdf_extra_time_1_05_1 = ECDF(list_sharing_duration[5][1])
ecdf_extra_time_05_1_1 = ECDF(list_sharing_duration[6][1])
ecdf_extra_time_1_1_1 = ECDF(list_sharing_duration[7][1])

fig, ax = plt.subplots()
ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_sharing_duration))])
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
ax.set_xlabel('taxi driver trip sharing duration (minutes)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(taxi_driver_sharing_duration_path)

'''
    Saving time
'''

ecdf_saving_time_05_05_05 = ECDF(list_sharing_duration[0][2])
ecdf_saving_time_1_05_05 = ECDF(list_sharing_duration[1][2])
ecdf_saving_time_05_1_05 = ECDF(list_sharing_duration[2][2])
ecdf_saving_time_05_05_1 = ECDF(list_sharing_duration[3][2])
ecdf_saving_time_1_1_05 = ECDF(list_sharing_duration[4][2])
ecdf_saving_time_1_05_1 = ECDF(list_sharing_duration[5][2])
ecdf_saving_time_05_1_1 = ECDF(list_sharing_duration[6][2])
ecdf_saving_time_1_1_1 = ECDF(list_sharing_duration[7][2])

fig, ax = plt.subplots()
ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,len(list_sharing_duration))])
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
ax.set_xlabel('transit passenger trip sharing duration (minutes)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(transit_passenger_sharing_duration_path)
