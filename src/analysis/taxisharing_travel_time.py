'''
    Analyse travel time of taxisharing routes
'''
from sys import argv
import pandas as pd
import numpy as np
import math

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from statsmodels.distributions.empirical_distribution import ECDF

sbwy_individual_trip_path = argv[1]
taxi_individual_trip_path = argv[2]
sbwy_taxi_maching_path = argv[3]
taxisharing_trip_path = argv[4]
# chart_name = argv[5]
# title_name = argv[6]

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

def walking_subway_distance_duration(df_sbwy_integration_destination):
    df_walking_positions = df_sbwy_integration_destination[df_sbwy_integration_destination['stop_id'].isnull()]
    df_sbwy_positions = df_sbwy_integration_destination[df_sbwy_integration_destination['stop_id'].isnull() == False]
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

    # print list_walking_distances
    #
    # print ''
    # print df_sbwy_positions
    sbwy_distance = df_sbwy_positions.iloc[-1]['distance'] - df_sbwy_positions.iloc[0]['distance']

    return {'walking_distance': list_walking_distances, 'sbwy_distance':sbwy_distance}

def sbwy_duration(df_sbwy_individual_trip, df_taxi_individual_trip, dict_matching, df_taxisharing_trip):

    list_sbwy_duration = []
    for match_id, match_route in dict_matching.iteritems():

        # select subway and taxi matching trips
        sbwy_matching_trip = [position for position in match_route if position['sequence'] < 7]
        taxi_matching_trip = [position for position in match_route if position['sequence'] >= 7]

        # sort sequence
        sbwy_matching_trip = sorted(sbwy_matching_trip, key=lambda position:position['sequence'])
        taxi_matching_trip = sorted(taxi_matching_trip, key=lambda position:position['sequence'])

        sbwy_trip_id = sbwy_matching_trip[0]['sampn_perno_tripno']
        taxi_trip_id = taxi_matching_trip[0]['sampn_perno_tripno']
        #print 'sbwy_trip_id', sbwy_trip_id
        #print 'taxi_trip_id', taxi_trip_id

        # taxi passenger individual route time
        # taxi_individual_trip = df_taxi_individual_trip[df_taxi_individual_trip['sampn_perno_tripno'] == taxi_trip_id]
        # taxi_individual_trip = taxi_individual_trip.sort_values(by='duration')

        # subway passenger individual route time
        sbwy_individual_trip = df_sbwy_individual_trip[df_sbwy_individual_trip['sampn_perno_tripno'] == sbwy_trip_id]
        sbwy_individual_trip = sbwy_individual_trip.sort_values(by='date_time')
        sbwy_origin_time = sbwy_individual_trip['date_time'].iloc[0]
        sbwy_individual_destination_time = sbwy_individual_trip['date_time'].iloc[-1]

        # find the integration position and time
        integration_position = 0
        for position in range(len(sbwy_individual_trip)):
            if sbwy_individual_trip.iloc[position]['date_time'] == sbwy_matching_trip[-1]['date_time']:
                integration_position = position
                break

        sbwy_walking_trip = sbwy_individual_trip.iloc[integration_position:]

        sbwy_integration_position = sbwy_individual_trip[sbwy_individual_trip['date_time'] == sbwy_matching_trip[-1]['date_time']]
        sbwy_integration_time = sbwy_integration_position['date_time'].iloc[0]

        # compute walking subway time
        dict_walking_sbwy_distances = walking_subway_distance_duration(sbwy_walking_trip)

        #print 'sbwy_passenger_origin', sbwy_origin_time
        #print 'sbwy_passenger_individual_destination', sbwy_individual_destination_time
        duration_individual = (sbwy_individual_destination_time - sbwy_integration_time).total_seconds()

        # subway passenger time with taxisharing
        taxisharing_route = df_taxisharing_trip[(df_taxisharing_trip['sbwy_sampn_perno_tripno'] == sbwy_trip_id)\
        & (df_taxisharing_trip['taxi_sampn_perno_tripno'] == taxi_trip_id)].iloc[0]

        sbwy_taxisharing_destination_time = taxisharing_route['last_destination_time']
        taxi_taxisharing_destination_time = taxisharing_route['first_destination_time']
        if taxisharing_route['sbwy_destination_first']:
            sbwy_taxisharing_destination_time = taxisharing_route['first_destination_time']
            taxi_taxisharing_destination_time = taxisharing_route['last_destination_time']
        duration_taxisharing = (sbwy_taxisharing_destination_time - sbwy_integration_time).total_seconds()

        #print 'sbwy_passenger_taxisharing_destination', sbwy_taxisharing_destination_time
        dict_sbwy_durantion = {'sbwy_trip_id': sbwy_trip_id, 'taxi_trip_id': taxi_trip_id,\
        'origin_date_time': sbwy_origin_time, 'first_walking_distance': dict_walking_sbwy_distances['walking_distance'][0],\
        'sbwy_distance': dict_walking_sbwy_distances['sbwy_distance'], 'last_walking_distance': dict_walking_sbwy_distances['walking_distance'][1],\
        'duration_individual': duration_individual, 'duration_taxisharing': duration_taxisharing}
        list_sbwy_duration.append(dict_sbwy_durantion)
        #print dict_sbwy_durantion
        #break

    df_sbwy_duration = pd.DataFrame(list_sbwy_duration)
    df_sbwy_duration = df_sbwy_duration[['sbwy_trip_id', 'taxi_trip_id', 'origin_date_time',\
    'duration_individual', 'duration_taxisharing', 'first_walking_distance', 'sbwy_distance', 'last_walking_distance']]

    return df_sbwy_duration

def remove_outliers(list_data):
    std_data = np.std(list_data)
    list_new_data = []
    for data in list_data:
        if data <= std_data*2:
            list_new_data.append(data)
    return list_new_data

# read individual routes and format datetime
df_sbwy_individual_trip = pd.read_csv(sbwy_individual_trip_path)
df_taxi_individual_trip = pd.read_csv(taxi_individual_trip_path)
df_sbwy_individual_trip['date_time'] = pd.to_datetime(df_sbwy_individual_trip['date_time'])

# read group matches
df_sbwy_taxi_matching = pd.read_csv(sbwy_taxi_maching_path)
df_sbwy_taxi_matching['date_time'] = pd.to_datetime(df_sbwy_taxi_matching['date_time'])
dict_matching = group_df_rows(df_sbwy_taxi_matching, 'match_id')

# read format taxisharing trips
df_taxisharing_trip = pd.read_csv(taxisharing_trip_path)
df_taxisharing_trip['first_destination_time'] = pd.to_datetime(df_taxisharing_trip['first_destination_time'])
df_taxisharing_trip['last_destination_time'] = pd.to_datetime(df_taxisharing_trip['last_destination_time'])

# distinct sbwy travels
print 'unique individual sbwy', len(df_sbwy_individual_trip['sampn_perno_tripno'].unique())
print 'unique individual taxi', len(df_taxi_individual_trip['sampn_perno_tripno'].unique())

# subway individual taxisharing duration
df_sbwy_duration = sbwy_duration(df_sbwy_individual_trip, df_taxi_individual_trip, dict_matching, df_taxisharing_trip)

# find good and bad rideshaing
list_good_ids = []
count_good_taxisharing = 0
list_time_saving = []
list_time_wasting = []
for index, durations in df_sbwy_duration.iterrows():
    if durations['duration_taxisharing'] < durations['duration_individual']:
        count_good_taxisharing += 1
        time_saving = (durations['duration_individual'] - durations['duration_taxisharing'])/60
        list_time_saving.append(time_saving)
        list_good_ids.append({'sbwy_trip_id':durations['sbwy_trip_id'], 'taxi_trip_id':durations['taxi_trip_id']})
        print durations
    else:
        time_wasting = (durations['duration_taxisharing'] - durations['duration_individual'])/60
        list_time_wasting.append(time_wasting)

# df_good_ids = pd.DataFrame(list_good_ids)
#
# df_good_taxisharing = df_taxisharing_trip[df_taxisharing_trip['taxi_sampn_perno_tripno'].isin(df_good_ids['taxi_trip_id'].tolist())\
# & df_taxisharing_trip['sbwy_sampn_perno_tripno'].isin(df_good_ids['sbwy_trip_id'].tolist())]
# dict_good_taxisharing = df_good_taxisharing.T.to_dict()
# for key, taxisharing in dict_good_taxisharing.iteritems():
#     print taxisharing['taxi_sampn_perno_tripno'], taxisharing['sbwy_sampn_perno_tripno'], taxisharing['destination_destination_distance'],\
#     taxisharing['taxi_sbwy_integration_distance'], taxisharing['sbwy_destination_first'], taxisharing['integration_destination_distance']

## plot saving and wasting
# list_time_saving = remove_outliers(list_time_saving)
# list_time_wasting = remove_outliers(list_time_wasting)
#
# list_time_saving.sort()
# ecdf_time_saving = ECDF(list_time_saving)
#
# list_time_wasting.sort()
# ecdf_time_wasting = ECDF(list_time_wasting)
#
# fig, ax = plt.subplots()
# plt.plot(ecdf_time_saving.x, ecdf_time_saving.y, label='time saving')
# plt.plot(ecdf_time_wasting.x, ecdf_time_wasting.y, label='waste of time')
#
# #ax.xaxis.set_major_locator(ticker.MultipleLocator(30)) # set x sticks interal
# plt.grid()
# plt.legend(loc=4)
# ax.set_title(title_name)
# ax.set_xlabel('time in minutes')
# ax.set_ylabel('ECDF')
# plt.tight_layout()
# fig.savefig(chart_name)
