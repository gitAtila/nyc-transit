'''
    Radius and distinct trips
'''

from sys import argv
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from statsmodels.distributions.empirical_distribution import ECDF

temporal_spatial_1000_path = argv[1]
temporal_spatial_2000_path = argv[2]
temporal_spatial_3000_path = argv[3]
temporal_spatial_4000_path = argv[4]
temporal_spatial_5000_path = argv[5]
temporal_spatial_inf_path = argv[6]
#
result_path = argv[9]

def distinct_taxi_transit_pair(cost_path, dict_counts):
    df_cost = pd.read_csv(cost_path)
    dict_counts['taxi'].append(len(df_cost['taxi_id'].unique()))
    dict_counts['transit'].append(len(df_cost['transit_id'].unique()))
    dict_counts['pair'].append(len(df_cost.groupby(['taxi_id','transit_id']).count()))
    return dict_counts

dict_counts = dict()
dict_counts['taxi'] = []
dict_counts['transit'] = []
dict_counts['pair'] = []

dict_counts = distinct_taxi_transit_pair(temporal_spatial_1000_path, dict_counts)
dict_counts = distinct_taxi_transit_pair(temporal_spatial_2000_path, dict_counts)
dict_counts = distinct_taxi_transit_pair(temporal_spatial_3000_path, dict_counts)
dict_counts = distinct_taxi_transit_pair(temporal_spatial_4000_path, dict_counts)
dict_counts = distinct_taxi_transit_pair(temporal_spatial_5000_path, dict_counts)
dict_counts = distinct_taxi_transit_pair(temporal_spatial_inf_path, dict_counts)

df_counts = pd.DataFrame(dict_counts, )
df_counts = df_counts[['taxi', 'transit', 'pair']]
ax = df_counts.plot(kind='bar')
ax.xaxis.set_ticklabels(['1000', '2000', '3000', '4000', '5000', 'inf'])
fig = ax.get_figure()
fig.savefig(result_path, bbox_inches='tight')
