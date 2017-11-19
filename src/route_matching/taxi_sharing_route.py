'''
    Read matching and compute the rest of route
'''

from sys import argv, path
import os
path.insert(0, os.path.abspath("../map_routing"))
import pandas as pd
import osrm_routing as api_osrm
from datetime import datetime, timedelta

matching_path = argv[1]
result_path = argv[2]

osm = api_osrm.OSRM_routing('driving')

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

# read matching routes
df_matches = pd.read_csv(matching_path)
df_matches['date_time'] = pd.to_datetime(df_matches['date_time'])

print df_matches
