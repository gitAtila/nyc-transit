'''
    save the time of start and end of all gtfs trips
'''
from sys import argv, maxint
import pandas as pd

import gtfs_processing as gp

gtfs_zip_folder = argv[1]
result_path = argv[2]

transit_feed  = gp.TransitFeedProcessing(gtfs_zip_folder)
df_trips = transit_feed.trips()
df_stop_times = transit_feed.stop_times()
df_trips_start_end_times = transit_feed.trips_start_end_times(df_trips, df_stop_times)
df_trips_start_end_times = df_trips_start_end_times[['route_id','trip_id','start_time','end_time']]
df_trips_start_end_times.to_csv(result_path, index=False)
