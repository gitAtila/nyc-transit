'''
    Read Taxi Limousine Comision dataset, put times and positions in a correct format and select interested fields
'''
from sys import argv
from datetime import datetime, timedelta
import pandas as pd
import math
import csv

from otp_routing import OTP_routing

tlc_trips_path = argv[1]
result_path = argv[2]

gtfs_year = int(argv[3])
router_id = argv[4]

# df_tlc_trips = pd.read_csv(tlc_trips_path)
# print df_tlc_trips
def str_to_float(str_float):
    if len(str_float) == 0:
        return 0.0
    else:
        return float(str_float)

def equivalent_weekday(original_date_time, new_date_time):
    if original_date_time.weekday() == new_date_time.weekday():
        return new_date_time

    day_before = new_date_time
    day_after = new_date_time
    while day_before.weekday() != original_date_time.weekday()\
    and day_after.weekday() != original_date_time.weekday():
        day_after += timedelta(days=1)
        day_before -= timedelta(days=1)

    if day_before.weekday() == original_date_time.weekday():
        return day_before
    else:
        return day_after

otp = OTP_routing(router_id)

csv_out_file = open(result_path, 'wb')
csv_writer = csv.writer(csv_out_file, delimiter=',')
csv_writer.writerow(('sampn_perno_tripno', 'mode', 'trip_sequence',\
'pos_sequence','date_time', 'longitude', 'latitude', 'distance', 'stop_id'))

trip_id = 1
with open(tlc_trips_path) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    csv_headings = next(csv_reader)

    next(csv_reader) # empty line
    # print csv_headings
    #['vendor_name', 'Trip_Pickup_DateTime', 'Trip_Dropoff_DateTime', 'Passenger_Count', 'Trip_Distance',\
    # 'Start_Lon', 'Start_Lat', 'Rate_Code', 'store_and_forward', 'End_Lon', 'End_Lat', 'Payment_Type',\
    # 'Fare_Amt', 'surcharge', 'mta_tax', 'Tip_Amt', 'Tolls_Amt', 'Total_Amt']


    # read trip by trip
    for row in csv_reader:
        print(trip_id)

        dict_taxi_trip = dict()
        dict_taxi_trip['trip_id'] = trip_id
        trip_id += 1
        # for column in range(len(csv_headings)):
        #     dict_taxi_trip[csv_headings[column]] = row[column]

        dict_taxi_trip['date_time_origin'] = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
        # dict_taxi_trip['Trip_Dropoff_DateTime'] = datetime.strptime(dict_taxi_trip['Trip_Dropoff_DateTime'], '%Y-%m-%d %H:%M:%S')

        prefix_trip_id = dict_taxi_trip['date_time_origin'].month
        dict_taxi_trip['trip_id'] = str(prefix_trip_id) + '_' + str(dict_taxi_trip['trip_id'])

        dict_taxi_trip['lon_origin'] = float(row[5])
        dict_taxi_trip['lat_origin'] = float(row[6])
        dict_taxi_trip['lon_destination'] = float(row[9])
        dict_taxi_trip['lat_destination'] = float(row[10])

        # invalid positions
        if (dict_taxi_trip['lon_origin'] == 0 or dict_taxi_trip['lat_origin'] == 0\
        or dict_taxi_trip['lon_destination'] == 0 or dict_taxi_trip['lat_destination'] == 0):
            continue

        date_time_origin = dict_taxi_trip['date_time_origin']
        print 'date_time_origin', date_time_origin

        # find equivalent day in the GTFS's year
        gtfs_day = datetime(gtfs_year, date_time_origin.month, date_time_origin.day)
        new_day = equivalent_weekday(date_time_origin, gtfs_day)

        new_date_time_origin = datetime.combine(new_day.date(), date_time_origin.time())
        print 'new_date_time_origin', new_date_time_origin

        # origin position were informed
        if math.isnan(dict_taxi_trip['lon_origin']) == False and math.isnan(dict_taxi_trip['lon_destination']) == True:
            continue

        try:
        	passenger_otp_trip = otp.route_positions(dict_taxi_trip['lat_origin'], dict_taxi_trip['lon_origin'],\
        	dict_taxi_trip['lat_destination'], dict_taxi_trip['lon_destination'], 'CAR', new_date_time_origin)
        except: # mode unknown
        	passenger_otp_trip = []

        for passenger_trip in passenger_otp_trip:
        	if len(passenger_trip) > 0:
        		passenger_trip['sampn_perno_tripno'] = dict_taxi_trip['trip_id']
        		passenger_trip['mode'] = 'TAXI'
                csv_writer.writerow((passenger_trip['sampn_perno_tripno'], passenger_trip['mode'],\
                passenger_trip['trip_sequence'], passenger_trip['pos_sequence'],passenger_trip['date_time'],\
                passenger_trip['longitude'], passenger_trip['latitude'], passenger_trip['distance'],\
                passenger_trip['stop_id']))

        # if trip_id > 50:
        #     break

csv_out_file.close()
