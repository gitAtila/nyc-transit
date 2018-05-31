'''
    Evaluate pricing policies
'''

from sys import argv
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from statsmodels.distributions.empirical_distribution import ECDF

cost_05_05_05_path = argv[1]
cost_1_05_05_path = argv[2]
cost_05_1_05_path = argv[3]
cost_05_05_1_path = argv[4]
cost_1_1_05_path = argv[5]
cost_1_05_1_path = argv[6]
cost_05_1_1_path = argv[7]
cost_1_1_1_path = argv[8]
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

dict_counts = distinct_taxi_transit_pair(cost_05_05_05_path, dict_counts)
dict_counts = distinct_taxi_transit_pair(cost_1_05_05_path, dict_counts)
dict_counts = distinct_taxi_transit_pair(cost_05_1_05_path, dict_counts)
# dict_counts = distinct_taxi_transit_pair(cost_05_05_1_path, dict_counts)
dict_counts = distinct_taxi_transit_pair(cost_1_1_05_path, dict_counts)
# dict_counts = distinct_taxi_transit_pair(cost_1_05_1_path, dict_counts)
# dict_counts = distinct_taxi_transit_pair(cost_05_1_1_path, dict_counts)
dict_counts = distinct_taxi_transit_pair(cost_1_1_1_path, dict_counts)

df_counts = pd.DataFrame(dict_counts)
df_counts = df_counts[['taxi', 'transit', 'pair']]
df_counts.rename(columns={'taxi': 'Taxi', 'transit': 'Transit', 'pair': 'Pair'},\
inplace=True)
print df_counts
ax = df_counts.plot(kind='bar')
# ax.xaxis.set_ticklabels(['.5 .5 .5', '1 .5 .5', '.5 1 .5', '.5 .5 1',\
# '1 1 .5', '1 .5 1', '.5 1 1', '1 1 1'])
ax.xaxis.set_ticklabels(['.5 .5 .5', '1 .5 .5', '.5 1 .5', '1 1 .5', '1 1 1'])
ax.set_xlabel('Pricing Policies (Initial Costs, Integragion, Sharing)')
ax.set_ylabel('# of Distinct Trips')
fig = ax.get_figure()
fig.savefig(result_path + 'distinct_trips.png', bbox_inches='tight')
