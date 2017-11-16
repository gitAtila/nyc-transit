'''
    Compute taxi route from origin to integration position and to passengers destinations
'''

from sys import argv, path
import os
path.insert(0, os.path.abspath("../map_routing"))
import pandas as pd
import osrm_routing as api_osrm
from datetime import datetime, timedelta

matching_path = argv[1]
survey_processed_trips_path = argv[2]
result_path = argv[3]

osm = api_osrm.OSRM_routing('driving')

# read matching routes
df_matches = pd.read_csv(matching_path)
df_matches['taxi_date_time'] = pd.to_datetime(df_matches['taxi_date_time'])
df_matches['sbwy_date_time'] = pd.to_datetime(df_matches['sbwy_date_time'])

# read passenger destination positions
list_taxisharing_routes = []
df_trip_od = pd.read_csv(survey_processed_trips_path)
for index, matching in df_matches.iterrows():
    taxi_integration_acceptance_time = df_matches['taxi_date_time']
    sbwy_integration_acceptance_time = df_matches['sbwy_date_time']

    # test
    list_route = osm.street_routing_steps(matching['taxi_lon'], matching['taxi_lat'],\
    matching['sbwy_lon'], matching['sbwy_lat'])

    for step in list_route:
        print step
    # test
    stop

    # compute acceptance-integration route
    acceptance_integration_route = osm.street_routing(matching['taxi_lon'], matching['taxi_lat'],\
    matching['sbwy_lon'], matching['sbwy_lat'])
    print acceptance_integration_route

    # get destination positions
    taxi_sampn_perno_tripno = matching['taxi_trip_id'].split('_')
    sbwy_sampn_perno_tripno = matching['sbwy_trip_id'].split('_')

    taxi_trip = df_trip_od[(df_trip_od['sampn'] == int(taxi_sampn_perno_tripno[0]))\
    & (df_trip_od['perno'] == int(taxi_sampn_perno_tripno[1]))\
    & (df_trip_od['tripno'] == int(taxi_sampn_perno_tripno[2]))].iloc[0]

    sbwy_trip = df_trip_od[(df_trip_od['sampn'] == int(sbwy_sampn_perno_tripno[0]))\
    & (df_trip_od['perno'] == int(sbwy_sampn_perno_tripno[1]))\
    & (df_trip_od['tripno'] == int(sbwy_sampn_perno_tripno[2]))].iloc[0]

    # compute integration-first_destination route
    integration_taxi_destination = osm.street_routing(matching['sbwy_lon'], matching['sbwy_lat'],\
    taxi_trip['lon_destination'], taxi_trip['lat_destination'])
    print integration_taxi_destination

    integration_sbwy_destination = osm.street_routing(matching['sbwy_lon'], matching['sbwy_lat'],\
    sbwy_trip['lon_destination'], sbwy_trip['lat_destination'])
    print integration_sbwy_destination

    # find which destination comes first
    if integration_taxi_destination['distance'] <= integration_sbwy_destination['distance']:
        first_destination = taxi_trip
        last_destination = sbwy_trip
        sbwy_destination_first = False
    else:
        first_destination = sbwy_trip
        last_destination = taxi_trip
        sbwy_destination_first = True

    # compute first_destination-last_destination route
    first_destination_last_destination = osm.street_routing(first_destination['lon_destination'],\
    first_destination['lat_destination'], last_destination['lon_destination'], last_destination['lat_destination'])
    print first_destination_last_destination

    distance_acceptance_integration = acceptance_integration_route['distance']
    taxi_station_arrival_time = matching['taxi_date_time']\
    + timedelta(seconds=acceptance_integration_route['duration'])


    if taxi_station_arrival_time > matching['sbwy_date_time']:
        taxi_station_departure_time = taxi_station_arrival_time
    else:
        taxi_station_departure_time = matching['sbwy_date_time']

    if sbwy_destination_first == True:
        distance_integration_destination = integration_sbwy_destination['distance']
        first_destination_arrival_time = taxi_station_departure_time\
        + timedelta(seconds=integration_sbwy_destination['duration'])
    else:
        distance_integration_destination = integration_taxi_destination['distance']
        first_destination_arrival_time = taxi_station_departure_time\
        + timedelta(seconds=integration_taxi_destination['duration'])
    distance_destination_destination = first_destination_last_destination['distance']
    last_destination_arrival_time = first_destination_arrival_time\
    + timedelta(seconds=first_destination_last_destination['duration'])

    print 'distance_acceptance_integration', distance_acceptance_integration
    print 'distance_integration_destination', distance_integration_destination
    print 'distance_destination_destination', distance_destination_destination
    print 'sbwy_destination_first', sbwy_destination_first
    print 'taxi_acceptance_time', matching['taxi_date_time']
    print 'sbwy_arrival_time', matching['sbwy_date_time']

    print 'taxi_station_arrival_time', taxi_station_arrival_time
    print 'taxi_station_departure_time', taxi_station_departure_time
    print 'first_destination_arrival_time', first_destination_arrival_time
    print 'last_destination_arrival_time', last_destination_arrival_time
    print '==================================='

    dict_ridesharing = {'taxi_trip_id': matching['taxi_trip_id'], 'sbwy_trip_id': matching['sbwy_trip_id'],\
    'distance_acceptance_integration': distance_acceptance_integration,\
    'distance_integration_destination': distance_integration_destination,\
    'distance_destination_destination': distance_destination_destination,\
    'sbwy_destination_first': sbwy_destination_first, 'sbwy_arrival_time': matching['sbwy_date_time'],\
    'taxi_acceptance_time': matching['taxi_date_time'],'taxi_station_arrival_time': taxi_station_arrival_time,\
    'taxi_station_departure_time': taxi_station_departure_time, 'first_destination_arrival_time': first_destination_arrival_time,\
    'last_destination_arrival_time': last_destination_arrival_time}

    list_taxisharing_routes.append(dict_ridesharing)
    #break

df_taxisharing = pd.DataFrame(list_taxisharing_routes)
df_taxisharing = df_taxisharing[['taxi_trip_id', 'sbwy_trip_id', 'distance_acceptance_integration', 'distance_integration_destination',\
'distance_destination_destination', 'sbwy_destination_first', 'taxi_acceptance_time', 'sbwy_arrival_time','taxi_station_arrival_time',\
'taxi_station_departure_time', 'first_destination_arrival_time', 'last_destination_arrival_time']]
df_taxisharing.to_csv(result_path, index_label='id')
