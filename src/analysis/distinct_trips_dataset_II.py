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
plt.rcParams.update({'font.size': 16})

max_benefit_real_seg_path = argv[1]
max_benefit_real_prop_path = argv[2]

max_benefit_10min_5x_seg_path = argv[3]
max_benefit_10min_5x_prop_path = argv[4]

max_benefit_20min_5x_seg_path = argv[5]
max_benefit_20min_5x_prop_path = argv[6]

max_benefit_10min_10x_seg_path = argv[7]
max_benefit_10min_10x_prop_path = argv[8]

max_benefit_20min_10x_seg_path = argv[9]
max_benefit_20min_10x_prop_path = argv[10]
#
result_path = argv[11]

def distinct_taxi_transit_pair(dict_counts, max_benefit_seg_path, max_benefit_prop_path):
    df_max_benefit_seg = pd.read_csv(max_benefit_seg_path)
    df_max_benefit_prop = pd.read_csv(max_benefit_prop_path)

    dict_counts['max_benefit_seg'].append(len(df_max_benefit_seg.groupby(['taxi_id','transit_id']).count()))
    dict_counts['max_benefit_prop'].append(len(df_max_benefit_prop.groupby(['taxi_id','transit_id']).count()))
    return dict_counts

dict_counts = dict()
dict_counts['max_benefit_seg'] = []
dict_counts['max_benefit_prop'] = []

dict_counts = distinct_taxi_transit_pair(dict_counts, max_benefit_real_seg_path, max_benefit_real_prop_path)
dict_counts = distinct_taxi_transit_pair(dict_counts, max_benefit_10min_5x_seg_path, max_benefit_10min_5x_prop_path)
dict_counts = distinct_taxi_transit_pair(dict_counts, max_benefit_20min_5x_seg_path, max_benefit_20min_5x_prop_path)
dict_counts = distinct_taxi_transit_pair(dict_counts, max_benefit_10min_10x_seg_path, max_benefit_10min_10x_prop_path)
dict_counts = distinct_taxi_transit_pair(dict_counts, max_benefit_20min_10x_seg_path, max_benefit_20min_10x_prop_path)

df_counts = pd.DataFrame(dict_counts, index=['real', '5x_10min', '5x_20min', '10x_10min', '10x_20min'])
df_counts = df_counts[['max_benefit_seg', 'max_benefit_prop']]
# df_counts = df_counts[['max_benefit']]
print df_counts
ax = df_counts.plot(style=['*-','o-'])
ax.legend(['Segment pricing policy','Propotional pricing policy'], loc=4)
ax.xaxis.set_major_locator(ticker.MultipleLocator(1)) # set x sticks interal
ax.xaxis.set_ticklabels(['','real', '5x_10min', '5x_20min', '10x_10min', '10x_20min'], rotation=30)
ax.set_xlabel('Real and synthetic datasets')
ax.set_ylabel('Number of distinct integrations')
fig = ax.get_figure()
fig.savefig(result_path + 'max_benefit_dataset_II.pdf', bbox_inches='tight')
