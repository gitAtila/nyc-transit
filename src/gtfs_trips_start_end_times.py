'''
    save the time of start and end of all gtfs trips
'''
from sys import argv, maxint
import pandas as pd
import zipfile

#import gtfs_processing as gp

gtfs_zip_folder = argv[1]
result_path = argv[2]

def read_file_in_zip(gtfs_zip_folder, file_name):
    zip_file = zipfile.ZipFile(gtfs_zip_folder)
    df_csv = pd.read_csv(zip_file.open(file_name))
    return df_csv

def trips_start_end_times(df_trips, df_stop_times):
    list_start_end_times = []
    df_stop_times = df_stop_times[['trip_id', 'departure_time']]
    for index, trip in df_trips.iterrows():
        trip_id = trip['trip_id']
        times_trip = df_stop_times[df_stop_times['trip_id'] == trip_id]
        sorted_trip_time = times_trip.sort_values(by=['departure_time'])
        start_time = sorted_trip_time.iloc[0]['departure_time']
        end_time = sorted_trip_time.iloc[-1]['departure_time']
        list_start_end_times.append({'trip_id': trip_id, 'route_id': trip['route_id'],\
        'start_time': start_time, 'end_time':end_time})
        print list_start_end_times[-1]
    return pd.DataFrame(list_start_end_times)

df_trips = read_file_in_zip(gtfs_zip_folder, 'trips.txt')
df_stop_times = read_file_in_zip(gtfs_zip_folder, 'stop_times.txt')
df_trips_start_end_times = trips_start_end_times(df_trips, df_stop_times)
df_trips_start_end_times = df_trips_start_end_times[['route_id','trip_id','start_time','end_time']]
df_trips_start_end_times.to_csv(result_path, index=False)
