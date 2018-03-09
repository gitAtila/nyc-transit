'''
    Plot computed durations and distances
'''
from sys import argv
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from statsmodels.distributions.empirical_distribution import ECDF

computed_trips_path = argv[1]
result_path = argv[2]

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

def split_modals(dict_trips):
    dict_bus_trips = dict()
    dict_taxi_trips = dict()
    dict_subway_trips = dict()
    dict_bus_subway_trips = dict()

    for sampn_perno_tripno, list_trip in dict_trips.iteritems():
        df_trip = pd.DataFrame(list_trip)
        list_modes = list(df_trip['mode'].unique())
        if len(list_modes) == 1:
            if list_modes[0] == 'TAXI':
                dict_taxi_trips[sampn_perno_tripno] = list_trip
            elif list_modes[0] == 'BUS':
                dict_bus_trips[sampn_perno_tripno] = list_trip
            elif list_modes[0] == 'SUBWAY':
                dict_subway_trips[sampn_perno_tripno] = list_trip
        elif len(list_modes) == 2:
            if 'SUBWAY' in list_modes and 'WALK' in list_modes:
                dict_subway_trips[sampn_perno_tripno] = list_trip
            elif 'BUS' in list_modes and 'WALK' in list_modes:
                dict_bus_trips[sampn_perno_tripno] = list_trip
            elif 'BUS' in list_modes and 'SUBWAY' in list_modes:
                dict_bus_subway_trips[sampn_perno_tripno] = list_trip
        elif len(list_modes) == 3:
            if 'SUBWAY' in list_modes and 'BUS' in list_modes and 'WALK' in list_modes:
                dict_bus_subway_trips[sampn_perno_tripno] = list_trip

    return dict_bus_trips, dict_taxi_trips, dict_subway_trips, dict_bus_subway_trips

def trips_duration(dict_trips):
    list_durations = []
    for sampn_perno_tripno, list_trip in dict_trips.iteritems():
        time_delta = (list_trip[-1]['date_time'] - list_trip[0]['date_time']).total_seconds()/60
        if time_delta > 0:
            list_durations.append(time_delta)
    return list_durations

# read computed trips
df_computed_trips = pd.read_csv(computed_trips_path)
df_computed_trips['date_time'] =  pd.to_datetime(df_computed_trips['date_time'])
dict_trips = group_df_rows(df_computed_trips, 'sampn_perno_tripno')
print len(dict_trips)

# group trips by mode
dict_bus_trips, dict_taxi_trips, dict_subway_trips, dict_bus_subway_trips = split_modals(dict_trips)
print 'dict_bus_trips', len(dict_bus_trips)
print 'dict_taxi_trips', len(dict_taxi_trips)
print 'dict_subway_trips', len(dict_subway_trips)
print 'dict_bus_subway_trips', len(dict_bus_subway_trips)

# compute total travel duration
list_bus_durations = trips_duration(dict_bus_trips)
list_taxi_durations = trips_duration(dict_taxi_trips)
list_subway_durations = trips_duration(dict_subway_trips)
list_bus_subway_durations = trips_duration(dict_bus_subway_trips)

# plot durations
fig, ax = plt.subplots()

list_subway_durations.sort()
ecdf_subway = ECDF(list_subway_durations)
plt.plot(ecdf_subway.x, ecdf_subway.y, label='NYC Subway')

list_bus_subway_durations.sort()
ecdf_bus_subway = ECDF(list_bus_subway_durations)
plt.plot(ecdf_bus_subway.x, ecdf_bus_subway.y, label='Subway + Bus')

list_bus_durations.sort()
ecdf_bus = ECDF(list_bus_durations)
plt.plot(ecdf_bus.x, ecdf_bus.y, label='NY-MTA Bus (only)')

list_taxi_durations.sort()
ecdf_taxi = ECDF(list_taxi_durations)
plt.plot(ecdf_taxi.x, ecdf_taxi.y, label='Taxi')

ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x ticks as multiple of sixty
plt.grid()
plt.legend(loc=4)
# ax.set_title('')
ax.set_xlabel('Computed Trip Duration (minutes)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(result_path)