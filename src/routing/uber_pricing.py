'''
    Compute uber pricing given origin and destination positions
'''
from sys import argv
import pandas as pd

from uber_rides.session import Session
from uber_rides.client import UberRidesClient
import uber_rides.errors

import requests
import json

token = argv[1]
private_trips_path = argv[2]
result_path = argv[3]

def uber_prices(token, start_latitude, start_longitude, end_latitude, end_longitude):

    session = Session(server_token=token)
    client = UberRidesClient(session)
    try:
        response = client.get_price_estimates(
            start_latitude=start_latitude,
            start_longitude=start_longitude,
            end_latitude=end_latitude,
            end_longitude=end_longitude,
            seat_count=2
        )
    except uber_rides.errors.ClientError:
        print 'client error', 'start_latitude=', start_latitude,\
        'start_longitude=', start_longitude,\
        'end_latitude=', end_latitude,\
        'end_longitude=', end_longitude
        return ''

    estimate = response.json.get('prices')
    print estimate
    return estimate

df_all_trips = pd.read_csv(private_trips_path)
df_taxi_trips = df_all_trips[df_all_trips['MODE_G10'] == 7]
count_taxi_trips = len(df_taxi_trips)

list_estimatives = []
for index, trip in df_taxi_trips.iterrows():
    trip_id = str(trip['sampn']) + '_' + str(trip['perno']) + '_' + str(trip['tripno'])

    estimatives = uber_prices(token, trip['lat_origin'], trip['lon_origin'],\
    trip['lat_destination'], trip['lon_destination'])

    list_estimatives.append({'trip_id': trip_id, 'estimatives': estimatives})

    print count_taxi_trips
    count_taxi_trips -= 1
    break

df_pricing = pd.DataFrame(list_estimatives)
df_pricing = df_pricing[['trip_id', 'estimatives']]
df_pricing.to_csv(result_path)
