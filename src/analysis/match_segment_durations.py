'''
    Compute duration distributions of each trip segment
'''
from sys import argv
import pandas as pd

import matplotlib.pyplot as plt
from statsmodels.distributions.empirical_distribution import ECDF

private_trips = argv[1]
matches_path = argv[2]
transit_result_path = argv[3]
taxi_result_path = argv[4]


def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

def plot_relative_durations(list_private_durations, list_shared_durations, list_destination_durations, result_path):
    list_private_durations.sort()
    list_shared_durations.sort()
    list_destination_durations.sort()

    ecdf_private_durations = ECDF(list_private_durations)
    ecdf_shared_durations = ECDF(list_shared_durations)
    ecdf_destination_durations = ECDF(list_destination_durations)

    fig, ax = plt.subplots()
    plt.plot(ecdf_private_durations.x, ecdf_private_durations.y, label='private')
    plt.plot(ecdf_shared_durations.x, ecdf_shared_durations.y, label='shared')
    plt.plot(ecdf_destination_durations.x, ecdf_destination_durations.y, label='destination')

    plt.grid()
    plt.legend()
    ax.set_xlabel('segment duration / total duration')
    ax.set_ylabel('ECDF')
    plt.tight_layout()
    fig.savefig(result_path)

# read and transform
df_private = pd.read_csv(private_trips)
df_private['date_time'] = pd.to_datetime(df_private['date_time'])
print df_private

df_matches = pd.read_csv(matches_path)
print df_matches
df_matches['transit_destination_time'] = pd.to_datetime(df_matches['transit_destination_time'])
df_matches['taxi_destination_time'] = pd.to_datetime(df_matches['taxi_destination_time'])
df_matches['taxi_arrival_time_transit_stop'] = pd.to_datetime(df_matches['taxi_arrival_time_transit_stop'])

# compute durations
list_transit_private_duration = []
list_transit_shared_duration = []
list_transit_destination_duration = []

list_taxi_private_duration = []
list_taxi_shared_duration = []
list_taxi_destination_duration = []
for index, match in df_matches.iterrows():
    # private time
    df_transit_private_trip = df_private[df_private['sampn_perno_tripno']== match['transit_id']]
    transit_origin_datetime = df_transit_private_trip.loc[df_transit_private_trip['date_time'].idxmin()]['date_time']
    transit_integration_datetime = df_transit_private_trip[df_transit_private_trip['stop_id'] == match['stop_id']]['date_time'].iloc[0]
    transit_private_duration = (transit_integration_datetime - transit_origin_datetime).total_seconds()
    # list_transit_private_duration.append(transit_private_duration/60)

    df_taxi_private_trip = df_private[df_private['sampn_perno_tripno'] == match['taxi_id']]
    taxi_origin_datetime = df_taxi_private_trip.loc[df_taxi_private_trip['date_time'].idxmin()]['date_time']
    taxi_private_duration = (match['taxi_arrival_time_transit_stop'] - taxi_origin_datetime).total_seconds()
    # list_taxi_private_duration.append(taxi_private_duration/60)

    # waiting time
    if transit_integration_datetime < match['taxi_arrival_time_transit_stop']:
        transit_private_duration += (match['taxi_arrival_time_transit_stop'] - transit_integration_datetime).total_seconds()
        shared_origin_time = match['taxi_arrival_time_transit_stop']
    else:
        taxi_private_duration += (transit_integration_datetime - match['taxi_arrival_time_transit_stop']).total_seconds()
        shared_origin_time = transit_integration_datetime

    # shared and destination durations
    if match['taxi_destination_time'] < match['transit_destination_time']:
        shared_duration = (match['taxi_destination_time'] - shared_origin_time).total_seconds()
        taxi_destination_duration = 0
        transit_destination_duration = (match['transit_destination_time'] - match['taxi_destination_time']).total_seconds()
        if shared_duration < 0:
            print 'taxi_destination_time', match['taxi_destination_time']
            print 'shared_distance', match['shared_distance']
            print 'shared_origin_time', shared_origin_time
            print 'shared_duration', shared_duration

    elif match['taxi_destination_time'] > match['transit_destination_time']:
        shared_duration = (match['transit_destination_time'] - shared_origin_time).total_seconds()
        taxi_destination_duration = (match['taxi_destination_time'] - match['transit_destination_time']).total_seconds()
        transit_destination_duration = 0
        if shared_duration < 0:
            print 'transit_destination_time', match['transit_destination_time']
            print 'shared_distance', match['shared_distance']
            print 'shared_origin_time', shared_origin_time
            print 'shared_duration', shared_duration
    else:
        shared_duration = (match['transit_destination_time'] - shared_origin_time).total_seconds()
        taxi_destination_duration = 0
        transit_destination_duration = 0
        if shared_duration < 0:
            print 'taxi_destination_time', match['taxi_destination_time']
            print 'shared_distance', match['shared_distance']
            print 'shared_origin_time', shared_origin_time
            print 'shared_duration', shared_duration

    total_transit_duration = (match['transit_destination_time'] - transit_origin_datetime).total_seconds()
    total_taxi_duration = (match['taxi_destination_time'] - taxi_origin_datetime).total_seconds()

    # compute and add to response relative durations
    list_transit_private_duration.append(float(transit_private_duration)/float(total_transit_duration))
    list_transit_shared_duration.append(float(shared_duration)/float(total_transit_duration))
    list_transit_destination_duration.append(float(transit_destination_duration)/float(total_transit_duration))

    list_taxi_private_duration.append(float(taxi_private_duration)/float(total_taxi_duration))
    list_taxi_shared_duration.append(float(shared_duration)/float(total_taxi_duration))
    list_taxi_destination_duration.append(float(taxi_destination_duration)/float(total_taxi_duration))

plot_relative_durations(list_transit_private_duration, list_transit_shared_duration, list_transit_destination_duration, transit_result_path)
plot_relative_durations(list_taxi_private_duration, list_taxi_shared_duration, list_taxi_destination_duration, taxi_result_path)
