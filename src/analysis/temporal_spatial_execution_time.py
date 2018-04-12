'''
    Read clock execution time files and plot results
'''
from sys import argv
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from statsmodels.distributions.empirical_distribution import ECDF

matching_1_path = argv[1]
matching_2_path = argv[2]
matching_3_path = argv[3]
matching_4_path = argv[4]
matching_5_path = argv[5]
matching_inf_path = argv[6]

clock_times_1_path = argv[7]
clock_times_2_path = argv[8]
clock_times_3_path = argv[9]
clock_times_4_path = argv[10]
clock_times_5_path = argv[11]
clock_times_inf_path = argv[12]

xlabel = argv[13]
chart_path = argv[14]
chart_file = argv[15]

colormap = plt.cm.nipy_spectral

# read clock times
# split matched from unmatched
def clock_times_matched_unmatched(matching_real_path, clock_times_real_path):
    df_matching = pd.read_csv(matching_real_path)
    df_clock_times = pd.read_csv(clock_times_real_path)
    # df_clock_times = df_clock_times.sort_valeus(by=['elapsed'])
    # df_clock_times['elapsed'] = df_clock_times['elapsed'] - df_clock_times['elapsed'].shift()

    print df_clock_times

    df_matched_times = df_clock_times[df_clock_times['transit_id'].isin(df_matching['transit_id'].tolist())]
    df_unmatched_times = df_clock_times[~df_clock_times['transit_id'].isin(df_matching['transit_id'].tolist())]

    return {'matched':df_matched_times['elapsed'], 'unmatched':df_unmatched_times['elapsed']}
    # print len(df_clock_times), len(df_matched_times), len(df_unmatched_times)
    # return {'matched':{'len': len(df_matched_times), 'mean': df_matched_times.mean(), 'std': df_matched_times.std()},\
    # 'unmatched':{'len': len(df_unmatched_times), 'mean': df_unmatched_times.mean(), 'std': df_unmatched_times.std()}}

def box_plot(data_to_plot, xlabel, chart_path):
    fig, ax = plt.subplots()
    plt.boxplot(data_to_plot)

    ax.set_xlabel(xlabel)
    ax.set_ylabel('clock time (seconds)')

    plt.xticks([1, 2, 3, 4, 5], [1000, 2000, 3000, 4000, 5000, 'inf'])
    # plt.xticks([1, 2, 3, 4, 5], ['real', '5x_10min', '5x_20min', '10x_10min', '10x_20min'])

    plt.tight_layout()
    fig.savefig(chart_path)

def ecdf_plot(list_times, chart_path):
    print chart_path

    ecdf_1 = ECDF(sorted(list_times[0]))
    ecdf_2 = ECDF(sorted(list_times[1]))
    ecdf_3 = ECDF(sorted(list_times[2]))
    ecdf_4 = ECDF(sorted(list_times[3]))
    ecdf_5 = ECDF(sorted(list_times[4]))
    ecdf_inf = ECDF(sorted(list_times[5]))

    fig, ax = plt.subplots()
    # ax.set_color_cycle([colormap(i) for i in np.linspace(0,1,5)])
    plt.plot(ecdf_1.x, ecdf_1.y, label='1km')
    plt.plot(ecdf_2.x, ecdf_2.y, label='2km')
    plt.plot(ecdf_3.x, ecdf_3.y, label='3km')
    plt.plot(ecdf_4.x, ecdf_4.y, label='4km')
    plt.plot(ecdf_5.x, ecdf_5.y, label='5km')
    plt.plot(ecdf_inf.x, ecdf_inf.y, label='inf')

    # ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
    # plt.grid()
    # plt.legend(loc=4)
    # ax.set_title('saturday')
    ax.set_xlabel('clock time (seconds)')
    ax.set_ylabel('ECDF')
    plt.tight_layout()
    fig.savefig(chart_path)


dict_statistics_1 = clock_times_matched_unmatched(matching_1_path, clock_times_1_path)
dict_statistics_2 = clock_times_matched_unmatched(matching_2_path, clock_times_2_path)
dict_statistics_3 = clock_times_matched_unmatched(matching_3_path, clock_times_3_path)
dict_statistics_4 = clock_times_matched_unmatched(matching_4_path, clock_times_4_path)
dict_statistics_5 = clock_times_matched_unmatched(matching_5_path, clock_times_5_path)
dict_statistics_inf = clock_times_matched_unmatched(matching_inf_path, clock_times_inf_path)

# xticks = [1000, 2000, 3000, 4000, 5000]
clock_time_matched = [dict_statistics_1['matched'].tolist(), dict_statistics_2['matched'].tolist(),\
dict_statistics_3['matched'].tolist(), dict_statistics_4['matched'].tolist(),\
dict_statistics_5['matched'].tolist(), dict_statistics_inf['matched'].tolist()]

clock_time_unmatched = [dict_statistics_1['unmatched'].tolist(), dict_statistics_2['unmatched'].tolist(),\
dict_statistics_3['unmatched'].tolist(), dict_statistics_4['unmatched'].tolist(),\
dict_statistics_5['unmatched'].tolist(), dict_statistics_inf['unmatched'].tolist()]

box_plot(clock_time_matched, xlabel, chart_path + 'matched_' + chart_file)
box_plot(clock_time_unmatched, xlabel, chart_path + 'unmatched_' + chart_file)

ecdf_plot(clock_time_matched, chart_path + 'cdf_matched_' + chart_file)
ecdf_plot(clock_time_unmatched, chart_path + 'cdf_unmatched_' + chart_file)
