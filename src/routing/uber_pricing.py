'''
    Compute uber pricing given origin and destination positions
'''
from sys import argv
import pandas as pd

from uber_rides.session import Session
from uber_rides.client import UberRidesClient

import requests
import json

token = argv[1]
private_trips_path = argv[2]

def uber_prices(token, start_latitude, start_longitude, end_latitude, end_longitude):

    session = Session(server_token=token)
    client = UberRidesClient(session)

    response = client.get_price_estimates(
        start_latitude=start_latitude,
        start_longitude=start_longitude,
        end_latitude=end_latitude,
        end_longitude=end_longitude,
        seat_count=2
    )

    estimate = response.json.get('prices')
    print estimate
    return estimate

df_all_trips = pd.read_csv(private_trips_path)
df_taxi_trips = df_all_trips[df_all_trips['MODE_G10'] == 7]

for index, trip in df_taxi_trips.iterrows():
    trip_id = trip['sampn_perno_tripno']

    estimatives = uber_prices(token, trip['lat_origin'], trip['lon_origin'],\
    trip['lat_destination'], trip['lon_destination'])

    print trip_id
    print estimatives

    break
