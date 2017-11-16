'''
    get routes from positions of origin and destination
'''

from sys import argv, path
import os
path.insert(0, os.path.abspath("../map_routing"))
import pandas as pd

import osrm_routing as api_osrm

taxi_trip_path = argv[1]
result_path = argv[2]

osm = api_osrm.OSRM_routing('driving')

df_taxi_trips = pd.read_csv(taxi_trip_path)

list_taxi_trip_route = []
for index, taxi_trip in df_taxi_trips.iterrows():

     trip_route = osm.street_routing_steps(taxi_trip['lon_origin'],taxi_trip['lat_origin'],\
     taxi_trip['lon_destination'], taxi_trip['lat_destination'])

     for step in trip_route:
         step['sampn_perno_tripno'] = taxi_trip['sampn_perno_tripno']
         list_taxi_trip_route.append(step)

df_taxi_trips = pd.DataFrame(list_taxi_trip_route)
df_taxi_trips = df_taxi_trips[['sampn_perno_tripno', 'distance','duration','latitude','longitude' ]]
print df_taxi_trips
df_taxi_trips.to_csv(result_path, index_label = 'id')
