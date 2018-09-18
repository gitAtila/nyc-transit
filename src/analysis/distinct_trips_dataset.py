'''
    Datasets and distinct trips
'''

from sys import argv
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from statsmodels.distributions.empirical_distribution import ECDF

temporal_spatial_real_path = argv[1]
cost_real_path = argv[2]
max_benefit_real_path = argv[3]

temporal_spatial_10min_5x_path = argv[4]
cost_10min_5x_path = argv[5]
max_benefit_10min_5x_path = argv[6]

temporal_spatial_20min_5x_path = argv[7]
cost_20min_5x_path = argv[8]
max_benefit_20min_5x_path = argv[9]

temporal_spatial_10min_10x_path = argv[10]
cost_10min_10x_path = argv[11]
max_benefit_10min_10x_path = argv[12]

temporal_spatial_20min_10x_path = argv[13]
cost_20min_10x_path = argv[14]
max_benefit_20min_10x_path = argv[15]
#
result_path = argv[16]

def distinct_taxi_transit_pair(dict_counts, temporal_spatial_path, cost_path, max_benefit_path):
    df_temporal_spatial = pd.read_csv(temporal_spatial_path)
    df_cost = pd.read_csv(cost_path)
    df_max_benefit = pd.read_csv(max_benefit_path)

    dict_counts['temporal_spatial'].append(len(df_temporal_spatial.groupby(['taxi_id','transit_id']).count()))
    dict_counts['cost'].append(len(df_cost.groupby(['taxi_id','transit_id']).count()))
    dict_counts['max_benefit'].append(len(df_max_benefit.groupby(['taxi_id','transit_id']).count()))
    return dict_counts

dict_counts = dict()
dict_counts['temporal_spatial'] = []
dict_counts['cost'] = []
dict_counts['max_benefit'] = []

dict_counts = distinct_taxi_transit_pair(dict_counts, temporal_spatial_real_path, cost_real_path, max_benefit_real_path)
dict_counts = distinct_taxi_transit_pair(dict_counts, temporal_spatial_10min_5x_path, cost_10min_5x_path, max_benefit_10min_5x_path)
dict_counts = distinct_taxi_transit_pair(dict_counts, temporal_spatial_20min_5x_path, cost_20min_5x_path, max_benefit_20min_5x_path)
dict_counts = distinct_taxi_transit_pair(dict_counts, temporal_spatial_10min_10x_path, cost_10min_10x_path, max_benefit_10min_10x_path)
dict_counts = distinct_taxi_transit_pair(dict_counts, temporal_spatial_20min_10x_path, cost_20min_10x_path, max_benefit_20min_10x_path)

df_counts = pd.DataFrame(dict_counts, index=['real', '5x_10min', '5x_20min', '10x_10min', '10x_20min'])
df_counts = df_counts[['temporal_spatial', 'cost', 'max_benefit']]
# df_counts = df_counts[['max_benefit']]
print df_counts
ax = df_counts.plot(kind='line')
# ax = df_counts.plot()
# ax.xaxis.set_major_locator(ticker.MultipleLocator(1)) # set x sticks interal
# ax.xaxis.set_ticklabels(['real', '5x_10min', '5x_20min', '10x_10min', '10x_20min'])
fig = ax.get_figure()
fig.savefig(result_path, bbox_inches='tight')
