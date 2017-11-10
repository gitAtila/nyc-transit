'''
    Compare informed and computed trip duration time
'''
from sys import argv
from datetime import datetime, timedelta
import pandas as pd

import gtfs_processing as gp

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from statsmodels.distributions.empirical_distribution import ECDF

sbwy_passenger_trips_path = argv[1]
sbwy_gtfs_path = argv[2]
sbwy_trip_times_path = argv[3]
day_type = argv[4]
survey_trips_path = argv[5]
chart_name = argv[6]

# read gtfs
sbwy_feed = gp.TransitFeedProcessing(sbwy_gtfs_path, sbwy_trip_times_path, int(day_type))
# read subway passenger trips
df_sbwy_passenger_trips = pd.read_csv(sbwy_passenger_trips_path)

df_stop_times = sbwy_feed.get_stop_times()
# filter used subway trips
list_gtfs_trip_id = list(set(df_sbwy_passenger_trips['gtfs_trip_id'].tolist()))
df_stop_times = df_stop_times[df_stop_times['trip_id'].isin(list_gtfs_trip_id)]
#print df_stop_times

# reconstruct passenger_route
def reconstruct_passenger_route(df_sbwy_passenger_trips, df_stop_times):
    list_passenger_trip_id = set(df_sbwy_passenger_trips['sampn_perno_tripno'].tolist())
    dict_passenger_routes = dict()
    for passenger_trip_id in list_passenger_trip_id:
        df_sbwy_passenger_route = df_sbwy_passenger_trips[df_sbwy_passenger_trips['sampn_perno_tripno'] == passenger_trip_id]
        df_sbwy_passenger_route = df_sbwy_passenger_route.sort_values('trip_sequence')

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
            list_passenger_trip = sorted(list_passenger_trip, key=lambda stop: stop['stop_sequence'])
            dict_passenger_routes.setdefault(passenger_trip_id, []).append(list_passenger_trip)

    return dict_passenger_routes

# read subway survey
df_survey_trips = pd.read_csv(survey_trips_path)
df_survey_trips[df_survey_trips['MODE_G10'] == 1]
list_survey_trips = []

dict_sbwy_passenger_routes = reconstruct_passenger_route(df_sbwy_passenger_trips, df_stop_times)
list_sbwy_computed_route_duration = []
list_sbwy_informed_route_duration = []
for sampn_perno_tripno, list_sbwy_trip_route in dict_sbwy_passenger_routes.iteritems():
    if len(list_sbwy_trip_route[0]) > 0 and len(list_sbwy_trip_route[-1]) > 0:
        computed_origin_time = list_sbwy_trip_route[0][0]['departure_time']
        computed_destination_time = list_sbwy_trip_route[-1][-1]['departure_time']

        computed_origin_time = timedelta(hours=computed_origin_time.hour, minutes=computed_origin_time.minute,\
         seconds=computed_origin_time.second, microseconds=computed_origin_time.microsecond)
        computed_destination_time = timedelta(hours=computed_destination_time.hour, minutes=computed_destination_time.minute,\
         seconds=computed_destination_time.second, microseconds=computed_destination_time.microsecond)

        if computed_destination_time < computed_origin_time:
            computed_destination_time += timedelta(hours=24)

        computed_duration = (computed_destination_time - computed_origin_time).total_seconds()/60
        list_sbwy_computed_route_duration.append(computed_duration)

        splited_sampn_perno_tripno = sampn_perno_tripno.split('_')
        person_survey_trip = df_survey_trips[(df_survey_trips['sampn'] == int(splited_sampn_perno_tripno[0]))\
         & (df_survey_trips['perno'] == int(splited_sampn_perno_tripno[1]))\
         & (df_survey_trips['tripno'] == int(splited_sampn_perno_tripno[2]))].iloc[0]
        #list_survey_trips.append(person_survey_trip)

        date_origin = person_survey_trip['trip_sdate'].split(' ')[0]
        time_origin = person_survey_trip['dtime']
        date_destination = person_survey_trip['trip_edate'].split(' ')[0]
        time_destination = person_survey_trip['atime']

        try:
            informed_origin_time = datetime.strptime(date_origin + ' ' + time_origin, '%m/%d/%y %H:%M')
            informed_destination_time = datetime.strptime(date_destination + ' ' + time_destination, '%m/%d/%y %H:%M')
        except ValueError:

            print 'Date error'
            print '"'+ date_origin +'"'+ time_origin +'"'
            print '"'+ date_destination +'"'+ time_destination +'"'

            destination_hour = time_destination.split(':')[0]
            if time_origin == '99:99':# and (destination_hour == '01' or destination_hour == '00'):
                time_origin = '00:00'
                informed_origin_time = datetime.strptime(date_origin + ' ' + time_origin, '%m/%d/%y %H:%M')
                informed_destination_time = datetime.strptime(date_destination + ' ' + time_destination, '%m/%d/%y %H:%M')

            origin_hour = time_origin.split(':')[0]
            if time_destination == '99:99':# and origin_hour == '23':
                time_destination = '00:00'
                informed_origin_time = datetime.strptime(date_origin + ' ' + time_origin, '%m/%d/%y %H:%M')
                informed_destination_time = datetime.strptime(date_destination + ' ' + time_destination, '%m/%d/%y %H:%M')

        if informed_destination_time < informed_origin_time:
            informed_destination_time += timedelta(hours=24)

        informed_duration = (informed_destination_time - informed_origin_time).total_seconds()/60
        if informed_duration > 0:
            list_sbwy_informed_route_duration.append(informed_duration)

        if informed_duration < 0:
            print person_survey_trip
            print informed_duration
            print informed_origin_time, informed_destination_time
        if computed_duration < 0:
            print list_sbwy_trip_route
            print computed_duration
            print computed_origin_time, computed_destination_time

print len(list_sbwy_computed_route_duration)
print len(list_sbwy_informed_route_duration)

for index in range(len(list_sbwy_computed_route_duration)):
    if list_sbwy_computed_route_duration[index] > 300:
        list_sbwy_computed_route_duration[index] = 300

for index in range(len(list_sbwy_informed_route_duration)):
    if list_sbwy_informed_route_duration[index] > 300:
        list_sbwy_informed_route_duration[index] = 300

list_sbwy_computed_route_duration.sort()
ecdf_computed_duration = ECDF(list_sbwy_computed_route_duration)

list_sbwy_informed_route_duration.sort()
ecdf_informed_duration = ECDF(list_sbwy_informed_route_duration)

fig, ax = plt.subplots()
plt.plot(ecdf_computed_duration.x, ecdf_computed_duration.y, label='computed duration')
plt.plot(ecdf_informed_duration.x, ecdf_informed_duration.y, label='informed duration')

#ax.xaxis.set_major_locator(ticker.MultipleLocator(60)) # set x sticks interal
plt.grid()
plt.legend()
ax.set_title('Subway Trips on Sunday')
ax.set_xlabel('Travel Duration in Minutes')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(chart_name)
