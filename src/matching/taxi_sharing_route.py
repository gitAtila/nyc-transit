'''
    Read matching and compute the rest of route through streets
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

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

# read matching routes
df_matches = pd.read_csv(matching_path)
df_matches['date_time'] = pd.to_datetime(df_matches['date_time'])

dict_matches = group_df_rows(df_matches, 'match_id')

df_trip_od = pd.read_csv(survey_processed_trips_path)

list_taxisharing = []
for match_id, match_route in dict_matches.iteritems():
    print match_id
    # select subway and taxi matching trips
    sbwy_matching_trip = [position for position in match_route if position['sequence'] < 7]
    taxi_matching_trip = [position for position in match_route if position['sequence'] >= 7]
    # sort sequence
    sbwy_matching_trip = sorted(sbwy_matching_trip, key=lambda position:position['sequence'])
    taxi_matching_trip = sorted(taxi_matching_trip, key=lambda position:position['sequence'])
    # get integration points
    sbwy_integration_point = sbwy_matching_trip[-1]
    taxi_integration_point = taxi_matching_trip[-1]

    # print sbwy_integration_point
    # print taxi_integration_point

    # compute acceptance-integration route
    acceptance_integration_route = osm.street_routing_geometry(taxi_integration_point['longitude'], taxi_integration_point['latitude'],\
    sbwy_integration_point['longitude'], sbwy_integration_point['latitude'])
    # print 'acceptance_integration_route'
    taxi_sbwy_integration_distance = acceptance_integration_route['distance']
    taxi_integration_arrival_time = taxi_integration_point['date_time'] + timedelta(seconds=acceptance_integration_route['duration'])
    sbwy_integration_arrival_time = sbwy_integration_point['date_time']
    taxi_integration_departure_time = taxi_integration_arrival_time
    # print acceptance_integration_route

    if sbwy_integration_arrival_time > taxi_integration_arrival_time:
        taxi_integration_departure_time = sbwy_integration_arrival_time

    # get taxi and subway destination positions
    taxi_sampn_perno_tripno = sbwy_integration_point['sampn_perno_tripno'].split('_')
    sbwy_sampn_perno_tripno = taxi_integration_point['sampn_perno_tripno'].split('_')

    taxi_survey_trip = df_trip_od[(df_trip_od['sampn'] == int(taxi_sampn_perno_tripno[0]))\
    & (df_trip_od['perno'] == int(taxi_sampn_perno_tripno[1]))\
    & (df_trip_od['tripno'] == int(taxi_sampn_perno_tripno[2]))].iloc[0]

    sbwy_survey_trip = df_trip_od[(df_trip_od['sampn'] == int(sbwy_sampn_perno_tripno[0]))\
    & (df_trip_od['perno'] == int(sbwy_sampn_perno_tripno[1]))\
    & (df_trip_od['tripno'] == int(sbwy_sampn_perno_tripno[2]))].iloc[0]

    # print taxi_survey_trip
    # print sbwy_survey_trip

    # compute integration-first_destination route
    integration_taxi_destination = osm.street_routing_geometry(sbwy_integration_point['longitude'], sbwy_integration_point['latitude'],\
    taxi_survey_trip['lon_destination'], taxi_survey_trip['lat_destination'])

    integration_sbwy_destination = osm.street_routing_geometry(sbwy_integration_point['longitude'], sbwy_integration_point['latitude'],\
    sbwy_survey_trip['lon_destination'], sbwy_survey_trip['lat_destination'])

    # find which destination comes first
    if integration_taxi_destination['distance'] <= integration_sbwy_destination['distance']:
        first_destination = taxi_survey_trip
        last_destination = sbwy_survey_trip
        sbwy_destination_first = False
        # print 'integration_first_destination'
        integration_destination_distance = integration_taxi_destination['distance']
        first_destination_time = taxi_integration_departure_time + timedelta(seconds=integration_taxi_destination['duration'])
        # print integration_taxi_destination
    else:
        first_destination = sbwy_survey_trip
        last_destination = taxi_survey_trip
        sbwy_destination_first = True
        # print 'integration_first_destination'
        integration_destination_distance = integration_sbwy_destination['distance']
        first_destination_time = taxi_integration_departure_time + timedelta(seconds=integration_sbwy_destination['duration'])
        # print integration_sbwy_destination

    # print 'sbwy_destination_first', sbwy_destination_first

    # compute first_destination-last_destination route
    first_destination_last_destination = osm.street_routing_geometry(first_destination['lon_destination'],\
    first_destination['lat_destination'], last_destination['lon_destination'], last_destination['lat_destination'])
    # print 'first_destination_last_destination'
    destination_destination_distance = first_destination_last_destination['distance']
    last_destination_time = first_destination_time + timedelta(seconds=first_destination_last_destination['duration'])
    # print first_destination_last_destination

    print 'taxi_sampn_perno_tripno', taxi_integration_point['sampn_perno_tripno']
    print 'sbwy_sampn_perno_tripno', sbwy_integration_point['sampn_perno_tripno']
    print 'taxi_sbwy_integration_distance', taxi_sbwy_integration_distance
    print 'taxi_integration_arrival_time', taxi_integration_arrival_time
    print 'taxi_integration_departure_time', taxi_integration_departure_time
    print 'sbwy_destination_first', sbwy_destination_first
    print 'integration_destination_distance', integration_destination_distance
    print 'first_destination_time', first_destination_time
    print 'destination_destination_distance', destination_destination_distance
    print 'last_destination_time', last_destination_time
    print '==================================='

    list_taxisharing.append({'taxi_sampn_perno_tripno': taxi_integration_point['sampn_perno_tripno'],\
    'sbwy_sampn_perno_tripno': sbwy_integration_point['sampn_perno_tripno'],\
    'taxi_sbwy_integration_distance': taxi_sbwy_integration_distance,\
    'taxi_integration_arrival_time': taxi_integration_arrival_time,\
    'taxi_integration_departure_time': taxi_integration_departure_time,\
    'sbwy_destination_first': sbwy_destination_first,\
    'integration_destination_distance': integration_destination_distance,\
    'first_destination_time': first_destination_time,\
    'destination_destination_distance': destination_destination_distance,\
    'last_destination_time': last_destination_time})

df_taxisharing_route = pd.DataFrame(list_taxisharing)
df_taxisharing_route = df_taxisharing_route[['taxi_sampn_perno_tripno', 'sbwy_sampn_perno_tripno',\
'taxi_sbwy_integration_distance', 'taxi_integration_arrival_time', 'taxi_integration_departure_time',\
'sbwy_destination_first', 'integration_destination_distance', 'first_destination_time',\
'destination_destination_distance', 'last_destination_time']]


df_taxisharing_route.to_csv(result_path, index=False)
