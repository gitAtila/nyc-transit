'''
    Using the same positions of origin and destination, generate n more trips
    by varying the size of the time window, t minutes more and less the time
    of origin
'''
from sys import argv, path, maxint
import os
path.insert(0, os.path.abspath("../routing"))
import pandas as pd
from datetime import datetime, timedelta
import numpy

all_trips_path = argv[1]
router_id = argv[2]
range_time = int(argv[3])
number_additional_trips = int(argv[4])
result_path = argv[5]

def inflate_trip(range_time, number_additional_trips, dict_trip):
    print type(dict_trip['date_time_origin'])
    date_time_origin = dict_trip['date_time_origin']
    # date_time_min = date_time_origin - timedelta(minutes=range_time)
    date_time_max = date_time_origin + timedelta(minutes=range_time)
    # print date_time_min
    print date_time_origin
    print date_time_max


# read taxi data
df_all_trips = pd.read_csv(all_trips_path)
df_taxi_trips = df_all_trips[df_all_trips['MODE_G10'] == 7]
df_taxi_trips['date_time_origin'] = pd.to_datetime(df_taxi_trips['date_time_origin'])
del df_all_trips

print df_taxi_trips
for index, trip in df_taxi_trips.iterrows():
    inflate_trip(range_time, number_additional_trips, trip.to_dict())
    break
# from one real trip generate n more with the same origin and destination


# save results
