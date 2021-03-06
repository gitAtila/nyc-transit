'''
    Show possibilities of integrations per trip
    python temporal_spatial_integrations.py ~/Documents/Projeto_2020/matching/transit_taxi/survey/temporal_spatial_real_inf.csv ~/Dropbox/Projeto_2020/resultados/
'''

from sys import argv
import pandas as pd

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from statsmodels.distributions.empirical_distribution import ECDF
plt.rcParams.update({'font.size': 16})

temporal_spatial_path = argv[1]
result_path = argv[2]

def plot_cdf_two_curves(list_curve_1, list_curve_2, label_curve_1, label_curve_2, x_label, chart_path):
    list_curve_1.sort()
    list_curve_2.sort()

    ecdf_curve_1 = ECDF(list_curve_1)
    ecdf_curve_2 = ECDF(list_curve_2)

    fig, ax = plt.subplots()
    plt.plot(ecdf_curve_1.x, ecdf_curve_1.y, label=label_curve_1)
    plt.plot(ecdf_curve_2.x, ecdf_curve_2.y, label=label_curve_2)

    ax.xaxis.set_major_locator(ticker.MultipleLocator(5)) # set x sticks interal
    plt.legend(loc=4)
    # ax.set_title('saturday')
    ax.set_xlabel(x_label)
    ax.set_ylabel('CDF')
    plt.tight_layout()
    fig.savefig(chart_path)

df_temporal_spatial = pd.read_csv(temporal_spatial_path)

list_taxi_per_transit = df_temporal_spatial.groupby('transit_id')['taxi_id'].nunique().tolist()
list_transit_per_taxi = df_temporal_spatial.groupby('taxi_id')['transit_id'].nunique().tolist()

list_transit_stop_options = df_temporal_spatial.groupby('transit_id')['stop_id'].nunique().tolist()
list_taxi_position_options = df_temporal_spatial.groupby('taxi_id')['taxi_pos_sequence'].nunique().tolist()

# plot_cdf_two_curves(list_transit_per_taxi, list_taxi_per_transit, 'Mass transit per taxi',\
# 'Taxi per mass transit', 'Number of trip options', result_path + 'cdf_integration_options_trips.eps')
#
# plot_cdf_two_curves(list_transit_stop_options, list_taxi_position_options, 'Mass transit stops',
# 'Taxi positions', 'Number of position options', result_path + 'cdf_integration_options_positions.eps')

plot_cdf_two_curves(list_transit_per_taxi, list_taxi_per_transit, 'Mass transit per taxi',\
'Taxi per mass transit', 'Number of trip options', result_path + 'cdf_integration_options_trips.pdf')

plot_cdf_two_curves(list_transit_stop_options, list_taxi_position_options, 'Mass transit stops',
'Taxi positions', 'Number of position options', result_path + 'cdf_integration_options_positions.pdf')
