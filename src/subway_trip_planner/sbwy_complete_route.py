'''
    Compute total subway travel
'''

from sys import argv, maxint
import pandas as pd
import geopandas as gpd
from geopy.distance import vincenty
from datetime import datetime, timedelta
import gtfs_processing as gp

survey_processed_trips_path = argv[1]
sbwy_passenger_trips_path = argv[2]
sbwy_gtfs_path = argv[3]
sbwy_trip_times_path = argv[4]

origin_boarding_times_path = argv[5]
alighting_destination_times_path = argv[6]

day_type = argv[7]

gtfs_transit_links_path = argv[8]

result_path = argv[9]

# reconstruct passenger_route
def reconstruct_passenger_route(df_sbwy_passenger_trips, df_stop_times):
    list_passenger_trip_id = set(df_sbwy_passenger_trips['sampn_perno_tripno'].tolist())
    dict_passenger_routes = dict()

    for passenger_trip_id in list_passenger_trip_id:
        # trips of the same travel
        df_sbwy_passenger_route = df_sbwy_passenger_trips[df_sbwy_passenger_trips['sampn_perno_tripno'] == passenger_trip_id]
        df_sbwy_passenger_route = df_sbwy_passenger_route.sort_values('trip_sequence')

        list_passenger_trips = []
        for index, passenger_trip in df_sbwy_passenger_route.iterrows():
            # select timestable of subway trip
            df_sbwy_trip = df_stop_times[df_stop_times['trip_id'] == passenger_trip['gtfs_trip_id']]
            # select times and stops of passenger boading until alight
            boarding_stop = df_sbwy_trip[df_sbwy_trip['stop_id'] == passenger_trip['boarding_stop_id']]
            alighting_stop = df_sbwy_trip[df_sbwy_trip['stop_id'] == passenger_trip['alighting_stop_id']]
            boarding_index = int(boarding_stop.index[0])
            alighting_index = int(alighting_stop.index[0])
            df_sbwy_trip = df_sbwy_trip.loc[boarding_index: alighting_index]
            # convert stop times in a list of dictionaries
            list_passenger_trip = df_sbwy_trip[['departure_time', 'stop_id', 'stop_sequence']].T.to_dict().values()
            list_passenger_trips.append(sorted(list_passenger_trip, key=lambda stop: stop['stop_sequence']))

        dict_passenger_routes[passenger_trip_id] = list_passenger_trips

    return dict_passenger_routes

def trip_from_sampn_perno_tripno(df_trips, sampn_perno_tripno):
    sampn_perno_tripno = sampn_perno_tripno.split('_')
    informed_trip = df_trips[(df_trips['sampn'] == int(sampn_perno_tripno[0]))\
     & (df_trips['perno'] == int(sampn_perno_tripno[1]))\
     & (df_trips['tripno'] == int(sampn_perno_tripno[2]))]
    return informed_trip

def add_time_to_date(origin_time, list_steps):
    list_position_time = []
    for step in list_steps:
        step_time = origin_time + timedelta(seconds=step['duration'])
        step['date_time'] = step_time
    return list_steps

def combine_walking_subway_route(arrival_boarding_datetime, list_sbwy_trip_route,\
list_origin_boarding_walking, list_alighting_destination_walking, df_stops, df_transit_links):
    list_sbwy_complete_route = []
    for pos_time in list_origin_boarding_walking:
        list_sbwy_complete_route.append({'longitude': pos_time['longitude'], 'latitude': pos_time['latitude'],\
        'date_time': pos_time['date_time'], 'distance': pos_time['distance'], 'stop_id': ''})

    #print arrival_datetime

    previous_distance = 0.0
    for list_stop in list_sbwy_trip_route:
        previous_stop_id = ''
        for stop in list_stop:
            stop_data = df_stops[df_stops['stop_id'] == stop['stop_id']].iloc[0]
            # add date to stop time
            stop_time = stop['departure_time']
            if stop_time > arrival_boarding_datetime.time():
                stop_datetime = datetime.combine(arrival_boarding_datetime.date(), stop_time)
            else:
                stop_date = arrival_boarding_datetime.date() + timedelta(days=1)
                stop_datetime = datetime.combine(stop_date, stop_time)
            #print stop_datetime
            if previous_stop_id == '':
                list_sbwy_complete_route.append({'longitude': stop_data['stop_lon'], 'latitude': stop_data['stop_lat'],\
                'date_time': stop_datetime, 'distance': previous_distance, 'stop_id': stop['stop_id']})
            else:

                link = df_transit_links[(df_transit_links['from_stop_id'] == previous_stop_id) \
                & (df_transit_links['to_stop_id'] == stop['stop_id'])]

                if len(link) > 0:
                    distance = previous_distance + link['shape_len'].iloc[0]
                    list_sbwy_complete_route.append({'longitude': stop_data['stop_lon'], 'latitude': stop_data['stop_lat'],\
                    'date_time': stop_datetime, 'distance': distance, 'stop_id': stop['stop_id']})
                    previous_distance = distance
                else:
                    list_sbwy_complete_route.append({'longitude': stop_data['stop_lon'], 'latitude': stop_data['stop_lat'],\
                    'date_time': stop_datetime, 'distance': previous_distance, 'stop_id': stop['stop_id']})

            previous_stop_id = stop['stop_id']

    for pos_time in list_alighting_destination_walking:
        list_sbwy_complete_route.append({'longitude': pos_time['longitude'], 'latitude': pos_time['latitude'],\
        'date_time': pos_time['date_time'], 'distance': pos_time['distance'], 'stop_id': ''})

    for route in list_sbwy_complete_route:
        print route
    print '\n'
    return list_sbwy_complete_route

def group_trip_positions(df_trip_positions):
    dict_trip_positions = dict()
    for index, position in df_trip_positions.iterrows():
        dict_trip_positions.setdefault(position['sampn_perno_tripno'], [])\
        .append({'distance': position['distance'],'duration': position['duration'],
        'latitude': position['latitude'], 'longitude': position['longitude']})
    return dict_trip_positions

# read trips
df_trips = pd.read_csv(survey_processed_trips_path)
df_trips = df_trips[(df_trips['MODE_G10'] == 1)|(df_trips['MODE_G10'] == 7)]
df_trips['date_time_origin'] = pd.to_datetime(df_trips['date_time_origin'])
df_trips['date_time_destination'] = pd.to_datetime(df_trips['date_time_destination'])

# read gtfs
sbwy_feed = gp.TransitFeedProcessing(sbwy_gtfs_path, sbwy_trip_times_path, int(day_type))
# read subway passenger trips
df_sbwy_passenger_trips = pd.read_csv(sbwy_passenger_trips_path)
df_transit_links = pd.read_csv(gtfs_transit_links_path)

df_stop_times = sbwy_feed.get_stop_times()
df_stops = sbwy_feed.get_stops()

# filter used subway trips
list_gtfs_trip_id = list(set(df_sbwy_passenger_trips['gtfs_trip_id'].tolist()))
df_stop_times = df_stop_times[df_stop_times['trip_id'].isin(list_gtfs_trip_id)]
#print df_stop_times

dict_sbwy_passenger_routes = reconstruct_passenger_route(df_sbwy_passenger_trips, df_stop_times)

# read walking distances
dict_origin_boarding_walking = group_trip_positions(pd.read_csv(origin_boarding_times_path))
dict_alighting_destination_walking = group_trip_positions(pd.read_csv(alighting_destination_times_path))

# iterating over subway passenger routes
list_all_subway_routes = []
for sbwy_sampn_perno_tripno, list_sbwy_trip_route in dict_sbwy_passenger_routes.iteritems():

    if len(list_sbwy_trip_route[0]) > 0:

        # get informed travel data
        informed_sbwy_trip = trip_from_sampn_perno_tripno(df_trips, sbwy_sampn_perno_tripno)
        informed_sbwy_origin_time = informed_sbwy_trip['date_time_origin'].iloc[0]
        informed_sbwy_destination_time = informed_sbwy_trip['date_time_destination'].iloc[0]

        print list_sbwy_trip_route

        # compute subway travel data
        computed_sbwy_boarding_time = datetime.combine(informed_sbwy_origin_time.date(),\
        list_sbwy_trip_route[0][0]['departure_time'])

        if list_sbwy_trip_route[0][0]['departure_time'] <= list_sbwy_trip_route[-1][-1]['departure_time']:
            computed_sbwy_alighting_time = datetime.combine(informed_sbwy_origin_time.date(),\
            list_sbwy_trip_route[-1][-1]['departure_time'])
        else:
            alighting_date_time = informed_sbwy_origin_time + timedelta(days=1)
            computed_sbwy_alighting_time = datetime.combine(alighting_date_time.date(),\
            list_sbwy_trip_route[-1][-1]['departure_time'])

        subway_travel_duration = (computed_sbwy_alighting_time - computed_sbwy_boarding_time).total_seconds()

        # compute walking duration
        origin_boarding_duration = 0
        list_origin_boarding_walking = []
        if sbwy_sampn_perno_tripno in dict_origin_boarding_walking.keys():
            list_origin_boarding_walking = dict_origin_boarding_walking[sbwy_sampn_perno_tripno]
            origin_boarding_duration = list_origin_boarding_walking[-1]['duration']

        list_alighting_destination_walking = dict_alighting_destination_walking[sbwy_sampn_perno_tripno]

        alighting_destination_duration = list_alighting_destination_walking[-1]['duration']

        # compute subway destination time
        total_subway_route_duration = origin_boarding_duration + subway_travel_duration + alighting_destination_duration
        computed_sbwy_destination_time = informed_sbwy_origin_time + timedelta(seconds=total_subway_route_duration)

        if len(list_origin_boarding_walking) > 0:
            list_origin_boarding_walking = add_time_to_date(informed_sbwy_origin_time,\
            list_origin_boarding_walking)
            arrival_boarding_datetime = list_origin_boarding_walking[-1]['date_time']
        else:
            arrival_boarding_datetime = informed_sbwy_origin_time

        list_alighting_destination_walking = add_time_to_date(computed_sbwy_alighting_time,\
        list_alighting_destination_walking)

        list_sbwy_complete_route = combine_walking_subway_route(arrival_boarding_datetime,\
        list_sbwy_trip_route, list_origin_boarding_walking, list_alighting_destination_walking,\
        df_stops, df_transit_links)

        for sbwy_trip in list_sbwy_complete_route:
            sbwy_trip['sampn_perno_tripno'] = sbwy_sampn_perno_tripno
            list_all_subway_routes.append(sbwy_trip)

df_complete_routes = pd.DataFrame(list_all_subway_routes)
df_complete_routes = df_complete_routes[['sampn_perno_tripno' ,'date_time',  'longitude', 'latitude', 'stop_id', 'distance']]
print df_complete_routes
df_complete_routes.to_csv(result_path, index_label = 'id')
