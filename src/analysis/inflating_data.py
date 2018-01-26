'''
    Inflating data
'''

from sys import argv
import pandas as pd

search_time_10min_5x_3000_path = argv[1]
search_time_10min_10x_3000_path = argv[2]
search_time_20min_5x_3000_path = argv[3]
search_time_20min_10x_3000_path = argv[4]

temporal_spatial_match_10min_5x_3000_path = argv[5]
temporal_spatial_match_10min_10x_3000_path = argv[6]
temporal_spatial_match_20min_5x_3000_path = argv[7]
temporal_spatial_match_20min_10x_3000_path = argv[8]

def avg_match_time(search_time_path, temporal_spatial_match_path):
    df_search_time = pd.read_csv(search_time_path)
    print 'total_time', df_search_time['elapsed'].sum()

    df_temporal_spatial_match = pd.read_csv(temporal_spatial_match_path)

    df_matched_time = df_search_time[df_search_time['transit_id'].isin(df_temporal_spatial_match['transit_id'].tolist())]
    print '=> matched'
    print 'len', len(df_matched_time)
    print 'std', df_matched_time['elapsed'].std()
    print 'mean', df_matched_time['elapsed'].mean()

    df_unmatched_time = df_search_time[~df_search_time['transit_id'].isin(df_temporal_spatial_match['transit_id'].tolist())]
    print '=> unmatched'
    print 'len', len(df_unmatched_time)
    print 'std', df_unmatched_time['elapsed'].std()
    print 'mean', df_unmatched_time['elapsed'].mean()
    print '=================='

print '10min_5x_3000'
avg_match_time(search_time_10min_5x_3000_path, temporal_spatial_match_10min_5x_3000_path)
print '10min_10x_3000'
avg_match_time(search_time_10min_10x_3000_path, temporal_spatial_match_10min_10x_3000_path)
print '20min_5x_3000'
avg_match_time(search_time_20min_5x_3000_path, temporal_spatial_match_20min_5x_3000_path)
print '20min_10x_3000'
avg_match_time(search_time_20min_10x_3000_path, temporal_spatial_match_20min_10x_3000_path)
