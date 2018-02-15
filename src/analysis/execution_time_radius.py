'''
    Read clock execution time files and plot results
'''
from sys import argv
import pandas as pd
import matplotlib.pyplot as plt

matching_real_1k_path = argv[1]
matching_real_2k_path = argv[2]
matching_real_3k_path = argv[3]
matching_real_4k_path = argv[4]
matching_real_5k_path = argv[5]

clock_times_real_1k_path = argv[6]
clock_times_real_2k_path = argv[7]
clock_times_real_3k_path = argv[8]
clock_times_real_4k_path = argv[9]
clock_times_real_5k_path = argv[10]

chart_path = argv[11]
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

dict_statistics_1k = clock_times_matched_unmatched(matching_real_1k_path, clock_times_real_1k_path)
dict_statistics_2k = clock_times_matched_unmatched(matching_real_2k_path, clock_times_real_2k_path)
dict_statistics_3k = clock_times_matched_unmatched(matching_real_3k_path, clock_times_real_3k_path)
dict_statistics_4k = clock_times_matched_unmatched(matching_real_4k_path, clock_times_real_4k_path)
dict_statistics_5k = clock_times_matched_unmatched(matching_real_5k_path, clock_times_real_5k_path)

xticks = [1000, 2000, 3000, 4000, 5000]
data_to_plot = [dict_statistics_1k['matched'].tolist(), dict_statistics_2k['matched'].tolist(),\
dict_statistics_3k['matched'].tolist(), dict_statistics_4k['matched'].tolist(),\
dict_statistics_5k['matched'].tolist()]

fig, ax = plt.subplots()
plt.boxplot(data_to_plot)

ax.set_xlabel('radius (km)')
ax.set_ylabel('clock time (seconds)')

plt.tight_layout()
fig.savefig(chart_path + 'clock_time_radius.png')
