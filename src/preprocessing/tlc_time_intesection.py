'''
    Select tlc data that temporaly intersects transit dataset
'''
from sys import argv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import csv

transit_data_path = argv[1]
tlc_trips_path = argv[2]
reference_year = int(argv[3])
result_path = argv[4]

def equivalent_day(original_date_time, reference_year):
    # print original_date_time, type(original_date_time)
    # print reference_year, original_date_time.month, original_date_time.day
    try:
        new_date_time = datetime(reference_year, original_date_time.month, original_date_time.day)
        print new_date_time
        if original_date_time.weekday() == new_date_time.weekday():
            return datetime.combine(new_date_time.date(), original_date_time.time())

        day_before = new_date_time
        day_after = new_date_time
        while day_before.weekday() != original_date_time.weekday()\
        and day_after.weekday() != original_date_time.weekday():
            day_after += timedelta(days=1)
            day_before -= timedelta(days=1)

        if day_before.weekday() == original_date_time.weekday():
            return datetime.combine(day_before.date(), original_date_time.time())
        else:
            return datetime.combine(day_after.date(), original_date_time.time())

    except TypeError:
        return -1
    return -1

def od_overlap_trip(date_time_pickup, date_time_dropoff, df_transit_trips):
    df_overplaping = df_transit_trips[(df_transit_trips['date_time_origin'] <= date_time_dropoff)\
    & (df_transit_trips['date_time_destination'] >= date_time_pickup)]
    if len(df_overplaping) > 0:
        return True
    else:
        return False


df_transit_trips = pd.read_csv(transit_data_path)
df_transit_trips = df_transit_trips[df_transit_trips['MODE_G10'].isin([1,3])]
df_transit_trips = df_transit_trips[pd.isnull(df_transit_trips['date_time_origin']) == False]
df_transit_trips = df_transit_trips[pd.isnull(df_transit_trips['lat_origin']) == False]
df_transit_trips = df_transit_trips[pd.isnull(df_transit_trips['lon_destination']) == False]
df_transit_trips['date_time_origin'] = pd.to_datetime(df_transit_trips['date_time_origin'])
df_transit_trips['date_time_origin'] = df_transit_trips['date_time_origin']\
.apply(lambda x: equivalent_day(x, reference_year))
df_transit_trips['date_time_destination'] = pd.to_datetime(df_transit_trips['date_time_destination'])
df_transit_trips['date_time_destination'] = df_transit_trips['date_time_destination']\
.apply((lambda x: equivalent_day(x, reference_year)))

# print df_transit_trips
# stop
#

csv_out_file = open(result_path, 'wb')
csv_writer = csv.writer(csv_out_file, delimiter=',')

list_overlaped_taxi_trips = []
with open(tlc_trips_path) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    csv_headings = next(csv_reader)

    csv_writer.writerow(csv_headings)

    next(csv_reader) # empty line
    # print csv_headings
    #['vendor_name', 'Trip_Pickup_DateTime', 'Trip_Dropoff_DateTime', 'Passenger_Count', 'Trip_Distance',\
    # 'Start_Lon', 'Start_Lat', 'Rate_Code', 'store_and_forward', 'End_Lon', 'End_Lat', 'Payment_Type',\
    # 'Fare_Amt', 'surcharge', 'mta_tax', 'Tip_Amt', 'Tolls_Amt', 'Total_Amt']


    # read trip by trip
    for row in csv_reader:
        dict_trip = dict(zip(csv_headings, row))

        date_time_pickup = datetime.strptime(dict_trip['Trip_Pickup_DateTime'], '%Y-%m-%d %H:%M:%S')
        date_time_dropoff = datetime.strptime(dict_trip['Trip_Dropoff_DateTime'], '%Y-%m-%d %H:%M:%S')


        new_date_time_pickup = equivalent_day(date_time_pickup, reference_year)
        print 'new_date_time_pickup', new_date_time_pickup

        new_date_time_dropoff = equivalent_day(date_time_dropoff, reference_year)
        print 'new_date_time_dropoff', new_date_time_dropoff

        if od_overlap_trip(new_date_time_pickup, new_date_time_dropoff, df_transit_trips) == True:
            csv_writer.writerow(row)

csv_out_file.close()
