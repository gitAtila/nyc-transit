'''
    Read individual subway travel and compute walking distances and sbwy distance
'''
from sys import argv
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from statsmodels.distributions.empirical_distribution import ECDF

sbwy_individual_trip_path = argv[1]
chart_results_path = argv[2]

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

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

df_sbwy_individual_trip = pd.read_csv(sbwy_individual_trip_path)
df_sbwy_individual_trip['date_time'] = pd.to_datetime(df_sbwy_individual_trip['date_time'])
list_sampn_perno_tripno = df_sbwy_individual_trip['sampn_perno_tripno'].tolist()

list_sbwy_distances = []
list_sbwy_first_walking_distances = []
list_sbwy_last_walking_distances = []
for sampn_perno_tripno in list_sampn_perno_tripno:
    df_sbwy_trip = df_sbwy_individual_trip[df_sbwy_individual_trip['sampn_perno_tripno'] == sampn_perno_tripno]
    dict_distances = walking_subway_distances(df_sbwy_trip)
    list_sbwy_first_walking_distances.append(dict_distances['walking_distance'][0])
    list_sbwy_last_walking_distances.append(dict_distances['walking_distance'][1])
    list_sbwy_distances.append(dict_distances['sbwy_distance'])

print df_sbwy_individual_trip

# plot subway distances
list_sbwy_first_walking_distances = [distance/1000 for distance in list_sbwy_first_walking_distances]
list_sbwy_last_walking_distances = [distance/1000 for distance in list_sbwy_last_walking_distances]
list_sbwy_distances = [distance/1000 for distance in list_sbwy_distances]

list_sbwy_first_walking_distances.sort()
list_sbwy_last_walking_distances.sort()
list_sbwy_distances.sort()

ecdf_first_walking_distances = ECDF(list_sbwy_first_walking_distances)
ecdf_last_walking_distances = ECDF(list_sbwy_last_walking_distances)
ecdf_sbwy_distances = ECDF(list_sbwy_distances)

fig, ax = plt.subplots()
plt.plot(ecdf_first_walking_distances.x, ecdf_first_walking_distances.y, label='origin walking')
plt.plot(ecdf_last_walking_distances.x, ecdf_last_walking_distances.y, label='destination walking')
plt.plot(ecdf_sbwy_distances.x, ecdf_sbwy_distances.y, label='subway')

#ax.xaxis.set_major_locator(ticker.MultipleLocator(30)) # set x sticks interal
plt.grid()
plt.legend(loc=4)
#ax.set_title(title_name)
ax.set_xlabel('distance km')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(chart_results_path)
