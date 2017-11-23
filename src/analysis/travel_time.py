'''
    Analyse travel time of taxisharing routes
'''
from sys import argv
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from statsmodels.distributions.empirical_distribution import ECDF

sbwy_individual_trip_path = argv[1]
taxi_individual_trip_path = argv[2]
sbwy_taxi_maching_path = argv[3]
taxisharing_trip_path = argv[4]
chart_name = argv[5]
title_name = argv[6]

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

def sbwy_duration(df_sbwy_individual_trip, df_taxi_individual_trip, dict_matching, df_taxisharing_trip):

    list_sbwy_duration = []
    for match_id, match_route in dict_matching.iteritems():
        #print match_id
        # select subway and taxi matching trips
        sbwy_matching_trip = [position for position in match_route if position['sequence'] < 7]
        taxi_matching_trip = [position for position in match_route if position['sequence'] >= 7]

        # sort sequence
        sbwy_matching_trip = sorted(sbwy_matching_trip, key=lambda position:position['sequence'])
        taxi_matching_trip = sorted(taxi_matching_trip, key=lambda position:position['sequence'])

        sbwy_trip_id = sbwy_matching_trip[0]['sampn_perno_tripno']
        taxi_trip_id = taxi_matching_trip[0]['sampn_perno_tripno']
        #print 'sbwy_trip_id', sbwy_trip_id
        #print 'taxi_trip_id', taxi_trip_id

        # taxi passenger individual route time
        # taxi_individual_trip = df_taxi_individual_trip[df_taxi_individual_trip['sampn_perno_tripno'] == taxi_trip_id]
        # taxi_individual_trip = taxi_individual_trip.sort_values(by='duration')

        # subway passenger individual route time
        sbwy_individual_trip = df_sbwy_individual_trip[df_sbwy_individual_trip['sampn_perno_tripno'] == sbwy_trip_id]
        sbwy_individual_trip = sbwy_individual_trip.sort_values(by='date_time')
        sbwy_origin_time = sbwy_individual_trip['date_time'].iloc[0]
        sbwy_individual_destination_time = sbwy_individual_trip['date_time'].iloc[-1]

        #print 'sbwy_passenger_origin', sbwy_origin_time
        #print 'sbwy_passenger_individual_destination', sbwy_individual_destination_time
        duration_individual = (sbwy_individual_destination_time - sbwy_origin_time).total_seconds()

        # subway passenger time with taxisharing
        taxisharing_route = df_taxisharing_trip[(df_taxisharing_trip['sbwy_sampn_perno_tripno'] == sbwy_trip_id)\
        & (df_taxisharing_trip['taxi_sampn_perno_tripno'] == taxi_trip_id)].iloc[0]

        sbwy_taxisharing_destination_time = taxisharing_route['last_destination_time']
        taxi_taxisharing_destination_time = taxisharing_route['first_destination_time']
        if taxisharing_route['sbwy_destination_first']:
            sbwy_taxisharing_destination_time = taxisharing_route['first_destination_time']
            taxi_taxisharing_destination_time = taxisharing_route['last_destination_time']
        duration_taxisharing = (sbwy_taxisharing_destination_time - sbwy_origin_time).total_seconds()

        #print 'sbwy_passenger_taxisharing_destination', sbwy_taxisharing_destination_time
        dict_sbwy_durantion = {'sbwy_trip_id': sbwy_trip_id, 'taxi_trip_id': taxi_trip_id,\
        'origin_date_time': sbwy_origin_time, 'duration_individual': duration_individual,\
        'duration_taxisharing': duration_taxisharing}
        list_sbwy_duration.append(dict_sbwy_durantion)
        #print dict_sbwy_durantion
        #break

    df_sbwy_duration = pd.DataFrame(list_sbwy_duration)
    df_sbwy_duration = df_sbwy_duration[['sbwy_trip_id', 'taxi_trip_id', 'origin_date_time',\
    'duration_individual', 'duration_taxisharing']]

    return df_sbwy_duration

df_sbwy_individual_trip = pd.read_csv(sbwy_individual_trip_path)
df_taxi_individual_trip = pd.read_csv(taxi_individual_trip_path)

df_sbwy_individual_trip['date_time'] = pd.to_datetime(df_sbwy_individual_trip['date_time'])

df_sbwy_taxi_matching = pd.read_csv(sbwy_taxi_maching_path)
dict_matching = group_df_rows(df_sbwy_taxi_matching, 'match_id')

df_taxisharing_trip = pd.read_csv(taxisharing_trip_path)
df_taxisharing_trip['first_destination_time'] = pd.to_datetime(df_taxisharing_trip['first_destination_time'])
df_taxisharing_trip['last_destination_time'] = pd.to_datetime(df_taxisharing_trip['last_destination_time'])

# distinct sbwy travels
print 'unique individual sbwy', len(df_sbwy_individual_trip['sampn_perno_tripno'].unique())
print 'unique individual taxi', len(df_taxi_individual_trip['sampn_perno_tripno'].unique())

df_sbwy_duration = sbwy_duration(df_sbwy_individual_trip, df_taxi_individual_trip, dict_matching, df_taxisharing_trip)
#print df_sbwy_duration

count_good_taxisharing = 0
list_time_saving = []
list_good_duration_individual = []
list_good_duration_taxisharing = []
list_bad_duration_individual = []
list_bad_duration_taxisharing = []
for index, durations in df_sbwy_duration.iterrows():
    if durations['duration_taxisharing'] < durations['duration_individual']:
        count_good_taxisharing += 1
        time_saving = (durations['duration_individual'] - durations['duration_taxisharing'])/60
        list_time_saving.append(time_saving)

        list_good_duration_taxisharing.append(durations['duration_taxisharing'])
        list_good_duration_individual.append(durations['duration_individual'])
    else:
        list_bad_duration_taxisharing.append(durations['duration_taxisharing'])
        list_bad_duration_individual.append(durations['duration_individual'])

print len(df_sbwy_duration)
print count_good_taxisharing
print float(count_good_taxisharing)/len(df_sbwy_duration)
print 'statistics'
print 'mean', np.mean(list_time_saving)
print 'std', np.std(list_time_saving)
print 'var', np.var(list_time_saving)
print 'min', np.min(list_time_saving)
print 'max', np.max(list_time_saving)

# plot cdf
# list_sbwy_individual_route_duration = df_sbwy_duration['duration_individual'].tolist()
# list_sbwy_taxisharing_route_duration = df_sbwy_duration['duration_taxisharing'].tolist()

# list_sbwy_individual_route_duration = list_good_duration_individual
# list_sbwy_taxisharing_route_duration = list_good_duration_taxisharing

list_sbwy_individual_route_duration = list_bad_duration_individual
list_sbwy_taxisharing_route_duration = list_bad_duration_taxisharing

list_sbwy_individual_route_duration = [duration/60 for duration in list_sbwy_individual_route_duration]
list_sbwy_taxisharing_route_duration = [duration/60 for duration in list_sbwy_taxisharing_route_duration]

list_sbwy_taxisharing_route_duration.sort()
ecdf_taxisharing_duration = ECDF(list_sbwy_taxisharing_route_duration)

list_sbwy_individual_route_duration.sort()
ecdf_individual_duration = ECDF(list_sbwy_individual_route_duration)

fig, ax = plt.subplots()
plt.plot(ecdf_taxisharing_duration.x, ecdf_taxisharing_duration.y, label='taxisharing')
plt.plot(ecdf_individual_duration.x, ecdf_individual_duration.y, label='individual')

#ax.xaxis.set_major_locator(ticker.MultipleLocator(60)) # set x sticks interal
plt.grid()
plt.legend(loc=4)
ax.set_title(title_name)
ax.set_xlabel('Travel Duration in Minutes')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(chart_name)
