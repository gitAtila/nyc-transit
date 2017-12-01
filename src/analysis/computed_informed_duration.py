'''
    Compare informed and computed trip duration time
'''
from sys import argv
import pandas as pd
import numpy as np
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from statsmodels.distributions.empirical_distribution import ECDF

computed_trips_path = argv[1]
informed_trips_path = argv[2]
mode_code = int(argv[3])
chart_results_path = argv[4]

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

def trip_from_sampn_perno_tripno(df_trips, sampn_perno_tripno):
    sampn_perno_tripno = sampn_perno_tripno.split('_')
    informed_trip = df_trips[(df_trips['sampn'] == int(sampn_perno_tripno[0]))\
     & (df_trips['perno'] == int(sampn_perno_tripno[1]))\
     & (df_trips['tripno'] == int(sampn_perno_tripno[2]))]
    return informed_trip

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

def remove_outliers(list_data):
    std_data = np.std(list_data)
    list_new_data = []
    for data in list_data:
        if data <= std_data*2:
            list_new_data.append(data)
    return list_new_data

def walking_subway_distances(df_sbwy_trip):
    df_walking_positions = df_sbwy_trip[df_sbwy_trip['stop_id'].isnull()]
    df_sbwy_positions = df_sbwy_trip[df_sbwy_trip['stop_id'].isnull() == False]
    # print ''
    # print df_walking_positions
    list_walking_distances = []
    first_distance = df_walking_positions.iloc[0]['distance']
    previous_distance = first_distance

    for index, current in df_walking_positions.iloc[1:].iterrows():
        if current['distance'] == 0:
            total_distance = previous_distance - first_distance
            list_walking_distances.append(total_distance)
            first_distance = 0
        previous_distance = current['distance']
    total_distance = previous_distance - first_distance
    list_walking_distances.append(total_distance)

    if len(list_walking_distances) == 0:
        list_walking_distances.append(0.0)
        list_walking_distances.append(0.0)
    elif len(list_walking_distances) == 1:
        list_walking_distances = [0.0] + list_walking_distances

    sbwy_distance = df_sbwy_positions.iloc[-1]['distance'] - df_sbwy_positions.iloc[0]['distance']

    return {'walking_distance': list_walking_distances, 'sbwy_distance':sbwy_distance}

df_computed_trips = pd.read_csv(computed_trips_path)
df_computed_trips['date_time'] = pd.to_datetime(df_computed_trips['date_time'])

df_informed_trips = pd.read_csv(informed_trips_path)
df_informed_trips = df_informed_trips[df_informed_trips['MODE_G10'] == mode_code]
df_informed_trips['date_time_origin'] = pd.to_datetime(df_informed_trips['date_time_origin'])
df_informed_trips['date_time_destination'] = pd.to_datetime(df_informed_trips['date_time_destination'])

dict_computed_trips = group_df_rows(df_computed_trips, 'sampn_perno_tripno')

list_id_informed_greater = []
list_id_computed_greater = []

list_informed_durations = []
list_computed_durations = []
for sampn_perno_tripno, computed_positions in dict_computed_trips.iteritems():

    # compute informed duration
    informed_trip = trip_from_sampn_perno_tripno(df_informed_trips, sampn_perno_tripno)
    if informed_trip['date_time_destination'].iloc[0] > informed_trip['date_time_origin'].iloc[0]:
        informed_duration = (informed_trip['date_time_destination'].iloc[0] - informed_trip['date_time_origin'].iloc[0]).total_seconds()
        #print informed_duration
        informed_duration /= 60
        list_informed_durations.append(informed_duration)

    # compute computed duration
    sorted_positions = sorted(computed_positions, key=lambda position:position['date_time'])
    computed_duration = (sorted_positions[-1]['date_time'] - sorted_positions[0]['date_time']).total_seconds()
    #print computed_duration
    computed_duration /= 60
    list_computed_durations.append(computed_duration)

    # if informed_duration >= computed_duration:
    #     list_id_informed_greater.append(sampn_perno_tripno)
    # else:
    #     list_id_computed_greater.append(sampn_perno_tripno)

# list_computed_durations = remove_outliers(list_computed_durations)
# list_informed_durations = remove_outliers(list_informed_durations)

list_computed_durations.sort()
list_informed_durations.sort()

ecdf_computed_durations = ECDF(list_computed_durations)
ecdf_informed_durations = ECDF(list_informed_durations)

fig, ax = plt.subplots()
plt.plot(ecdf_computed_durations.x, ecdf_computed_durations.y, label='computed')
plt.plot(ecdf_informed_durations.x, ecdf_informed_durations.y, label='informed')

#ax.xaxis.set_major_locator(ticker.MultipleLocator(30)) # set x sticks interal
plt.grid()
plt.legend(loc=4)
#ax.set_title(title_name)
ax.set_xlabel('duation in minutes')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(chart_results_path)

# list_sbwy_distances = []
# list_sbwy_first_walking_distances = []
# list_sbwy_last_walking_distances = []
# for sampn_perno_tripno in list_id_computed_greater:
#     df_sbwy_trip = df_computed_trips[df_computed_trips['sampn_perno_tripno'] == sampn_perno_tripno]
#     dict_distances = walking_subway_distances(df_sbwy_trip)
#     if dict_distances['walking_distance'][0] > 0:
#         list_sbwy_first_walking_distances.append(dict_distances['walking_distance'][0])
#         list_sbwy_last_walking_distances.append(dict_distances['walking_distance'][1])
#         list_sbwy_distances.append(dict_distances['sbwy_distance'])
#
# # plot subway distances
# list_sbwy_first_walking_distances = [distance/1000 for distance in list_sbwy_first_walking_distances]
# list_sbwy_last_walking_distances = [distance/1000 for distance in list_sbwy_last_walking_distances]
# list_sbwy_distances = [distance/1000 for distance in list_sbwy_distances]
#
# list_sbwy_first_walking_distances.sort()
# list_sbwy_last_walking_distances.sort()
# list_sbwy_distances.sort()
#
# ecdf_first_walking_distances = ECDF(list_sbwy_first_walking_distances)
# ecdf_last_walking_distances = ECDF(list_sbwy_last_walking_distances)
# ecdf_sbwy_distances = ECDF(list_sbwy_distances)
#
# fig, ax = plt.subplots()
# plt.plot(ecdf_first_walking_distances.x, ecdf_first_walking_distances.y, label='origin walking')
# plt.plot(ecdf_last_walking_distances.x, ecdf_last_walking_distances.y, label='destination walking')
# plt.plot(ecdf_sbwy_distances.x, ecdf_sbwy_distances.y, label='subway')
#
# #ax.xaxis.set_major_locator(ticker.MultipleLocator(30)) # set x sticks interal
# plt.grid()
# plt.legend(loc=4)
# #ax.set_title(title_name)
# ax.set_xlabel('distance km')
# ax.set_ylabel('ECDF')
# plt.tight_layout()
# fig.savefig(chart_results_path)
