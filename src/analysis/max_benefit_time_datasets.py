'''
    Evaluate matchings for different datasets
'''

from sys import argv
import pandas as pd

import matplotlib.pyplot as plt
from statsmodels.distributions.empirical_distribution import ECDF
plt.rcParams.update({'font.size': 16})

taxi_private_real_path = argv[1]
taxi_private_10min_5x_path = argv[2]
taxi_private_10min_10x_path = argv[3]
taxi_private_20min_5x_path = argv[4]
taxi_private_20min_10x_path = argv[5]

max_benefit_real_path = argv[6]
max_benefit_10min_5x_path = argv[7]
max_benefit_10min_10x_path = argv[8]
max_benefit_20min_5x_path = argv[9]
max_benefit_20min_10x_path = argv[10]

result_path = argv[11]

def saving_extra_time(taxi_private_trips_path, df_max_benefit_trip):

    list_transit_passenger_bp_saving_time = []
    list_taxi_passenger_extra_time = []
    list_taxi_driver_extra_time = []

    df_taxi_private_trips = pd.read_csv(taxi_private_trips_path)
    df_taxi_private_trips = df_taxi_private_trips[df_taxi_private_trips['sampn_perno_tripno']\
    .isin(df_max_benefit_trip['taxi_id'].unique())]
    df_taxi_private_trips['date_time'] = pd.to_datetime(df_taxi_private_trips['date_time'])
    dict_taxi_private_trips = group_df_rows(df_taxi_private_trips, 'sampn_perno_tripno')

    df_max_benefit_trip['transit_original_destination_time'] = pd.to_datetime(df_max_benefit_trip['transit_original_destination_time'])
    df_max_benefit_trip['transit_destination_time'] = pd.to_datetime(df_max_benefit_trip['transit_destination_time'])
    df_max_benefit_trip['taxi_destination_time'] = pd.to_datetime(df_max_benefit_trip['taxi_destination_time'])

    for index, max_benefit_trip in df_max_benefit_trip.iterrows():
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

    return list_transit_passenger_bp_saving_time, list_taxi_passenger_extra_time, list_taxi_driver_extra_time

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

# df_taxi_private_trips = pd.read_csv(taxi_private_trips_path)
# df_taxi_private_trips['date_time'] = pd.to_datetime(df_taxi_private_trips['date_time'])
# df_taxi_private_trips = df_taxi_private_trips[df_taxi_private_trips['mode'] == 'TAXI']
# dict_taxi_private_trips = group_df_rows(df_taxi_private_trips, 'sampn_perno_tripno')

df_max_benefit_real = pd.read_csv(max_benefit_real_path)
df_max_benefit_10min_5x = pd.read_csv(max_benefit_10min_5x_path)
df_max_benefit_10min_10x = pd.read_csv(max_benefit_10min_10x_path)
df_max_benefit_20min_5x = pd.read_csv(max_benefit_20min_5x_path)
df_max_benefit_20min_10x = pd.read_csv(max_benefit_20min_10x_path)

print len(df_max_benefit_real)
print len(df_max_benefit_10min_5x)
print len(df_max_benefit_10min_10x)
print len(df_max_benefit_20min_5x)
print len(df_max_benefit_20min_10x)

# how much time did transit passengers pay more?
# how much time did taxi passengers saved?
list_bp_saving_time_real, list_tp_extra_time_real, list_td_extra_time_real\
= saving_extra_time(taxi_private_real_path, df_max_benefit_real)

list_bp_saving_time_10min_5x, list_tp_extra_time_10min_5x, list_td_extra_time_10min_5x\
= saving_extra_time(taxi_private_10min_5x_path, df_max_benefit_10min_5x)

list_bp_saving_time_10min_10x, list_tp_extra_time_10min_10x, list_td_extra_time_10min_10x\
= saving_extra_time(taxi_private_10min_10x_path, df_max_benefit_10min_10x)

list_bp_saving_time_20min_5x, list_tp_extra_time_20min_5x, list_td_extra_time_20min_5x\
= saving_extra_time(taxi_private_20min_5x_path, df_max_benefit_20min_5x)

list_bp_saving_time_20min_10x, list_tp_extra_time_20min_10x, list_td_extra_time_20min_10x\
= saving_extra_time(taxi_private_20min_10x_path, df_max_benefit_20min_10x)

'''
    Taxi passenger extra time
'''

list_tp_extra_time_real.sort()
list_tp_extra_time_10min_5x.sort()
list_tp_extra_time_10min_10x.sort()
list_tp_extra_time_20min_5x.sort()
list_tp_extra_time_20min_10x.sort()

ecdf_tp_extra_time_real = ECDF(list_tp_extra_time_real)
ecdf_tp_extra_time_10min_5x = ECDF(list_tp_extra_time_10min_5x)
ecdf_tp_extra_time_10min_10x = ECDF(list_tp_extra_time_10min_10x)
ecdf_tp_extra_time_20min_5x = ECDF(list_tp_extra_time_20min_5x)
ecdf_tp_extra_time_20min_10x = ECDF(list_tp_extra_time_20min_10x)

fig, ax = plt.subplots()
plt.plot(ecdf_tp_extra_time_real.x, ecdf_tp_extra_time_real.y, label='real')
plt.plot(ecdf_tp_extra_time_10min_5x.x, ecdf_tp_extra_time_10min_5x.y, label='10min_5x')
plt.plot(ecdf_tp_extra_time_10min_10x.x, ecdf_tp_extra_time_10min_10x.y, label='10min_10x')
plt.plot(ecdf_tp_extra_time_20min_5x.x, ecdf_tp_extra_time_20min_5x.y, label='20min_5x')
plt.plot(ecdf_tp_extra_time_20min_10x.x, ecdf_tp_extra_time_20min_10x.y, label='20min_10x')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
#plt.grid()
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('taxi passenger extra time (minutes)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(result_path + 'max_benefit_tp_extra_time.pdf')

'''
    Taxi driver extra time
'''

list_td_extra_time_real.sort()
list_td_extra_time_10min_5x.sort()
list_td_extra_time_10min_10x.sort()
list_td_extra_time_20min_5x.sort()
list_td_extra_time_20min_10x.sort()

ecdf_td_extra_time_real = ECDF(list_td_extra_time_real)
ecdf_td_extra_time_10min_5x = ECDF(list_td_extra_time_10min_5x)
ecdf_td_extra_time_10min_10x = ECDF(list_td_extra_time_10min_10x)
ecdf_td_extra_time_20min_5x = ECDF(list_td_extra_time_20min_5x)
ecdf_td_extra_time_20min_10x = ECDF(list_td_extra_time_20min_10x)

fig, ax = plt.subplots()
plt.plot(ecdf_td_extra_time_real.x, ecdf_td_extra_time_real.y, label='real')
plt.plot(ecdf_td_extra_time_10min_5x.x, ecdf_td_extra_time_10min_5x.y, label='10min_5x')
plt.plot(ecdf_td_extra_time_10min_10x.x, ecdf_td_extra_time_10min_10x.y, label='10min_10x')
plt.plot(ecdf_td_extra_time_20min_5x.x, ecdf_td_extra_time_20min_5x.y, label='20min_5x')
plt.plot(ecdf_td_extra_time_20min_10x.x, ecdf_td_extra_time_20min_10x.y, label='20min_10x')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
#plt.grid()
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('taxi driver extra time (minutes)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(result_path + 'max_benefit_td_extra_time.pdf')

'''
    Transit Passenger Saving time
'''

list_bp_saving_time_real.sort()
list_bp_saving_time_10min_5x.sort()
list_bp_saving_time_10min_10x.sort()
list_bp_saving_time_20min_5x.sort()
list_bp_saving_time_20min_10x.sort()

ecdf_bp_saving_time_real = ECDF(list_bp_saving_time_real)
ecdf_bp_saving_time_10min_5x = ECDF(list_bp_saving_time_10min_5x)
ecdf_bp_saving_time_10min_10x = ECDF(list_bp_saving_time_10min_10x)
ecdf_bp_saving_time_20min_5x = ECDF(list_bp_saving_time_20min_5x)
ecdf_bp_saving_time_20min_10x = ECDF(list_bp_saving_time_20min_10x)

fig, ax = plt.subplots()
plt.plot(ecdf_bp_saving_time_real.x, ecdf_bp_saving_time_real.y, label='real')
plt.plot(ecdf_bp_saving_time_10min_5x.x, ecdf_bp_saving_time_10min_5x.y, label='10min_5x')
plt.plot(ecdf_bp_saving_time_10min_10x.x, ecdf_bp_saving_time_10min_10x.y, label='10min_10x')
plt.plot(ecdf_bp_saving_time_20min_5x.x, ecdf_bp_saving_time_20min_5x.y, label='20min_5x')
plt.plot(ecdf_bp_saving_time_20min_10x.x, ecdf_bp_saving_time_20min_10x.y, label='20min_10x')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
#plt.grid()
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('transit passenger saving time (minutes)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(result_path + 'max_benefit_bp_extra_time.pdf')
