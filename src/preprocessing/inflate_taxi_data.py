'''
    Using the same positions of origin and destination, generate n more trips
    by varying the size of the time window, t minutes more and less the time
    of origin
'''
from sys import argv, path, maxint
import os
path.insert(0, os.path.abspath("../routing"))
<<<<<<< HEAD
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta
from random import randrange

=======
import pandas as pd
from datetime import datetime, timedelta
import numpy
>>>>>>> c60ec7aaadb1685c499f3ecd3c6b5e8ce93a06ac

all_trips_path = argv[1]
router_id = argv[2]
range_time = int(argv[3])
number_additional_trips = int(argv[4])
result_path = argv[5]

def inflate_trip(range_time, number_additional_trips, dict_trip):
<<<<<<< HEAD
    list_child_trips = []

    # print type(dict_trip['date_time_origin'])
    date_time_origin = dict_trip['date_time_origin']
    date_time_destination = dict_trip['date_time_destination']

    date_time_min = date_time_origin - timedelta(minutes=range_time)
    date_time_max = date_time_origin + timedelta(minutes=range_time)

    try:
        date_time_min = time.mktime(date_time_min.timetuple())
        date_time_max = time.mktime(date_time_max.timetuple())
    except ValueError:
        return[]
        # print type(date_time_min)
        # print type(date_time_max)

    for index in range(number_additional_trips):
        new_date_time_origin = datetime.fromtimestamp(randrange(date_time_min,date_time_max))
        diff_date_time = (new_date_time_origin - date_time_origin).total_seconds()
        # print date_time_origin, new_date_time_origin, diff_date_time

        new_date_time_destination = date_time_destination + timedelta(seconds=diff_date_time)
        # print date_time_destination, new_date_time_destination

        child_trip = dict_trip.copy()
        child_trip['date_time_origin'] = new_date_time_origin
        child_trip['date_time_destination'] = new_date_time_destination
        list_child_trips.append(child_trip)

    return list_child_trips
=======
    print type(dict_trip['date_time_origin'])
    date_time_origin = dict_trip['date_time_origin']
    # date_time_min = date_time_origin - timedelta(minutes=range_time)
    date_time_max = date_time_origin + timedelta(minutes=range_time)
    # print date_time_min
    print date_time_origin
    print date_time_max

>>>>>>> c60ec7aaadb1685c499f3ecd3c6b5e8ce93a06ac

# read taxi data
df_all_trips = pd.read_csv(all_trips_path)
df_taxi_trips = df_all_trips[df_all_trips['MODE_G10'] == 7]
<<<<<<< HEAD
del df_taxi_trips['id']
df_taxi_trips['date_time_origin'] = pd.to_datetime(df_taxi_trips['date_time_origin'])
df_taxi_trips['date_time_destination'] = pd.to_datetime(df_taxi_trips['date_time_destination'])
del df_all_trips

# from one real trip generate n more with the same origin and destination
list_inflated_trips = []
for index, trip in df_taxi_trips.iterrows():
    list_child_trips = inflate_trip(range_time, number_additional_trips, trip.to_dict())
    list_inflated_trips += list_child_trips
df_inflated_trips = pd.DataFrame(list_inflated_trips)

# save result
print df_inflated_trips
df_inflated_trips = df_inflated_trips[['sampn', 'perno', 'tripno', 'MODE_G10', 'NSUB', 'StopAreaNo',\
'date_time_origin', 'lon_origin', 'lat_origin','date_time_destination', 'lon_destination', 'lat_destination']]
df_inflated_trips.to_csv(result_path, index=False)
=======
df_taxi_trips['date_time_origin'] = pd.to_datetime(df_taxi_trips['date_time_origin'])
del df_all_trips

print df_taxi_trips
for index, trip in df_taxi_trips.iterrows():
    inflate_trip(range_time, number_additional_trips, trip.to_dict())
    break
# from one real trip generate n more with the same origin and destination


# save results
>>>>>>> c60ec7aaadb1685c499f3ecd3c6b5e8ce93a06ac
