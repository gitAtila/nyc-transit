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

temporal_spatial_1000_path = argv[1]
cost_1000_path = argv[2]
max_benefit_1000_path = argv[3]

temporal_spatial_2000_path = argv[4]
cost_2000_path = argv[5]
max_benefit_2000_path = argv[6]

temporal_spatial_3000_path = argv[7]
cost_3000_path = argv[8]
max_benefit_3000_path = argv[9]

temporal_spatial_4000_path = argv[10]
cost_4000_path = argv[11]
max_benefit_4000_path = argv[12]

temporal_spatial_5000_path = argv[13]
cost_5000_path = argv[14]
max_benefit_5000_path = argv[15]

temporal_spatial_inf_path = argv[16]
cost_inf_path = argv[17]
max_benefit_inf_path = argv[18]
#
result_path = argv[19]

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

dict_counts = distinct_taxi_transit_pair(dict_counts, temporal_spatial_1000_path, cost_1000_path, max_benefit_1000_path)
dict_counts = distinct_taxi_transit_pair(dict_counts, temporal_spatial_2000_path, cost_2000_path, max_benefit_2000_path)
dict_counts = distinct_taxi_transit_pair(dict_counts, temporal_spatial_3000_path, cost_3000_path, max_benefit_3000_path)
dict_counts = distinct_taxi_transit_pair(dict_counts, temporal_spatial_4000_path, cost_4000_path, max_benefit_4000_path)
dict_counts = distinct_taxi_transit_pair(dict_counts, temporal_spatial_5000_path, cost_5000_path, max_benefit_5000_path)
dict_counts = distinct_taxi_transit_pair(dict_counts, temporal_spatial_inf_path, cost_inf_path, max_benefit_inf_path)

df_counts = pd.DataFrame(dict_counts, index=['1000', '2000', '3000', '4000', '5000', 'inf'])
df_counts = df_counts[['temporal_spatial', 'cost', 'max_benefit']]
print df_counts
ax = df_counts.plot(kind='bar')
# ax = df_counts.plot()
# ax.xaxis.set_major_locator(ticker.MultipleLocator(1)) # set x sticks interal
# ax.xaxis.set_ticklabels(['1000', '5x_10min', '5x_20min', '10x_10min', '10x_20min'])
fig = ax.get_figure()
fig.savefig(result_path, bbox_inches='tight')
