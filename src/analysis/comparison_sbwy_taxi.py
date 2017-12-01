'''
    Compare travel distances and durations of subway and taxi travels
'''
from sys import argv
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from statsmodels.distributions.empirical_distribution import ECDF

sbwy_individual_trip_path = argv[1]
taxi_individual_trip_path = argv[2]
chart_results_path = argv[3]

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

def plot_cdf_two_curves(list_curve_1, list_curve_2, label_curve_1, label_curve_2, x_label, chart_path):
    list_curve_1.sort()
    list_curve_2.sort()

    ecdf_curve_1 = ECDF(list_curve_1)
    ecdf_curve_2 = ECDF(list_curve_2)

    fig, ax = plt.subplots()
    plt.plot(ecdf_curve_1.x, ecdf_curve_1.y, label=label_curve_1)
    plt.plot(ecdf_curve_2.x, ecdf_curve_2.y, label=label_curve_2)

    # ax.xaxis.set_major_locator(ticker.MultipleLocator(30)) # set x sticks interal
    plt.grid()
    plt.legend(loc=4)
    #ax.set_title(title_name)
    ax.set_xlabel(x_label)
    ax.set_ylabel('ECDF')
    plt.tight_layout()
    fig.savefig(chart_path)

def sbwy_taxi_distances(df_sbwy_individual_trip, df_taxi_individual_trip):
    list_sampn_perno_tripno = df_sbwy_individual_trip['sampn_perno_tripno'].tolist()
    # subway total distance
    list_sbwy_distances = []
    for sampn_perno_tripno in list_sampn_perno_tripno:
        df_sbwy_trip = df_sbwy_individual_trip[df_sbwy_individual_trip['sampn_perno_tripno'] == sampn_perno_tripno]
        dict_distances = walking_subway_distances(df_sbwy_trip)
        if dict_distances['walking_distance'][0] > 0:
            total_distance = dict_distances['walking_distance'][0] + dict_distances['walking_distance'][1] + dict_distances['sbwy_distance']
            list_sbwy_distances.append(total_distance)

    # taxi total distances
    dict_taxi_individual_trip = group_df_rows(df_taxi_individual_trip, 'sampn_perno_tripno')
    list_taxi_distances = []
    for sampn_perno_tripno, positions in dict_taxi_individual_trip.iteritems():
        sorted_positions = sorted(positions, key=lambda position:position['distance'])
        list_taxi_distances.append(sorted_positions[-1]['distance'])

    # In kilometers
    list_sbwy_distances = [distance/1000 for distance in list_sbwy_distances]
    list_taxi_distances = [distance/1000 for distance in list_taxi_distances]

    return list_sbwy_distances, list_taxi_distances

def sbwy_taxi_durations(df_sbwy_individual_trip, df_taxi_individual_trip):
    dict_sbwy_individual_trip = group_df_rows(df_sbwy_individual_trip, 'sampn_perno_tripno')
    list_sbwy_durations = []
    for sampn_perno_tripno, positions in dict_sbwy_individual_trip.iteritems():
        sorted_positions = sorted(positions, key=lambda position:position['date_time'])
        duration_minutes = (sorted_positions[-1]['date_time'] - sorted_positions[0]['date_time']).total_seconds()/60
        list_sbwy_durations.append(duration_minutes)

    dict_taxi_individual_trip = group_df_rows(df_taxi_individual_trip, 'sampn_perno_tripno')
    list_taxi_durations = []
    for sampn_perno_tripno, positions in dict_taxi_individual_trip.iteritems():
        sorted_durations = sorted(positions, key=lambda position:position['pos_sequence'])
        list_taxi_durations.append((sorted_durations[-1]['date_time'] - sorted_durations[0]['date_time']).total_seconds()/60)

    return list_sbwy_durations, list_taxi_durations

df_sbwy_individual_trip = pd.read_csv(sbwy_individual_trip_path)
df_sbwy_individual_trip['date_time'] = pd.to_datetime(df_sbwy_individual_trip['date_time'])

df_taxi_individual_trip = pd.read_csv(taxi_individual_trip_path)
df_taxi_individual_trip['date_time'] = pd.to_datetime(df_taxi_individual_trip['date_time'])

#list_sbwy_distances, list_taxi_distances = sbwy_taxi_distances(df_sbwy_individual_trip, df_taxi_individual_trip)
# plot_cdf_two_curves(list_sbwy_distances, list_taxi_distances, 'subway', 'taxi', 'distance km', chart_results_path)

list_sbwy_durations, list_taxi_durations = sbwy_taxi_durations(df_sbwy_individual_trip, df_taxi_individual_trip)
list_sbwy_durations = remove_outliers(list_sbwy_durations)
plot_cdf_two_curves(list_sbwy_durations, list_taxi_durations, 'subway', 'taxi', 'duration in minutes', chart_results_path)
# plot subway distances
