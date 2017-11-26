'''
    Compare informed and computed trip duration time
'''
from sys import argv
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from statsmodels.distributions.empirical_distribution import ECDF

sbwy_computed_trips_path = argv[1]
sbwy_informed_trips_path = argv[2]
chart_name = argv[3]

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

df_computed_trips = pd.read_csv(sbwy_computed_trips_path)
df_informed_trips = pd.read_csv(sbwy_informed_trips_path)

dict_computed_trips = group_df_rows(df_computed_trips, 'sampn_perno_tripno')
list_sbwy_durations = []

for sampn_perno_tripno, computed_positions in dict_computed_trips.iteritems():
    sorted_positions = sorted(computed_positions, key=lambda position:position['date_time'])
    duration_minutes = (sorted_positions[-1]['date_time'] - sorted_positions[0]['date_time']).total_seconds()/60
    list_sbwy_durations.append(duration_minutes)

list_sampn_perno_tripno = dict_computed_trips.keys()
print len(list_sampn_perno_tripno)
