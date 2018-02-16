'''
    Read clock execution time files and plot results
'''
from sys import argv
import pandas as pd
import matplotlib.pyplot as plt

matching_1_path = argv[1]
matching_2_path = argv[2]
matching_3_path = argv[3]
matching_4_path = argv[4]
matching_5_path = argv[5]

clock_times_1_path = argv[6]
clock_times_2_path = argv[7]
clock_times_3_path = argv[8]
clock_times_4_path = argv[9]
clock_times_5_path = argv[10]

xlabel = argv[11]
chart_path = argv[12]
chart_file = argv[13]
# read clock times
# split matched from unmatched
def clock_times_matched_unmatched(matching_real_path, clock_times_real_path):
    df_matching = pd.read_csv(matching_real_path)
    df_clock_times = pd.read_csv(clock_times_real_path)

    df_matched_times = df_clock_times[df_clock_times['transit_id'].isin(df_matching['transit_id'].tolist())]
    df_unmatched_times = df_clock_times[~df_clock_times['transit_id'].isin(df_matching['transit_id'].tolist())]

    return {'matched':df_matched_times['elapsed'], 'unmatched':df_unmatched_times['elapsed']}
    # print len(df_clock_times), len(df_matched_times), len(df_unmatched_times)
    # return {'matched':{'len': len(df_matched_times), 'mean': df_matched_times.mean(), 'std': df_matched_times.std()},\
    # 'unmatched':{'len': len(df_unmatched_times), 'mean': df_unmatched_times.mean(), 'std': df_unmatched_times.std()}}

def plot(data_to_plot, xlabel, chart_path):
    fig, ax = plt.subplots()
    plt.boxplot(data_to_plot)

    ax.set_xlabel(xlabel)
    ax.set_ylabel('clock time (seconds)')

    # plt.xticks([1, 2, 3, 4, 5], ['real', '5x_10min', '5x_20min', '10x_10min', '10x_20min'])

    plt.tight_layout()
    fig.savefig(chart_path)

dict_statistics_1 = clock_times_matched_unmatched(matching_1_path, clock_times_1_path)
dict_statistics_2 = clock_times_matched_unmatched(matching_2_path, clock_times_2_path)
dict_statistics_3 = clock_times_matched_unmatched(matching_3_path, clock_times_3_path)
dict_statistics_4 = clock_times_matched_unmatched(matching_4_path, clock_times_4_path)
dict_statistics_5 = clock_times_matched_unmatched(matching_5_path, clock_times_5_path)

# xticks = [1000, 2000, 3000, 4000, 5000]
clock_time_matched = [dict_statistics_1['matched'].tolist(), dict_statistics_2['matched'].tolist(),\
dict_statistics_3['matched'].tolist(), dict_statistics_4['matched'].tolist(),\
dict_statistics_5['matched'].tolist()]

clock_time_unmatched = [dict_statistics_1['unmatched'].tolist(), dict_statistics_2['unmatched'].tolist(),\
dict_statistics_3['unmatched'].tolist(), dict_statistics_4['unmatched'].tolist(),\
dict_statistics_5['unmatched'].tolist()]

plot(clock_time_matched, xlabel, chart_path + 'matched_' + chart_file)
plot(clock_time_unmatched, xlabel, chart_path + 'unmatched_' + chart_file)
