'''
    Analyse estimatives of time from transit car matching
'''

from sys import argv
import pandas as pd

transit_trips_path = argv[1]
car_trips_path = argv[2]
matching_trips_path = argv[3]
chart_path = argv[4]

def group_df_rows(df, key_label, sort_by_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    if sort_by_label:
        for key, list_dict in dict_grouped.iteritems():
            dict_grouped[key] = sorted(list_dict, key=lambda pos: pos[sort_by_label])
    return dict_grouped

def group_list_dict(list_dict, key_label):
    dict_grouped = dict()
    for item in list_dict:
        key = item[key_label]
        del item[key_label]
        dict_grouped.setdefault(key, []).append(item)
    return dict_grouped

df_matching_trips = pd.read_csv(matching_trips_path)
df_matching_trips['car_arrival_time_transit_stop'] = pd.to_datetime(df_matching_trips['car_arrival_time_transit_stop'])
df_matching_trips['transit_destination_time'] = pd.to_datetime(df_matching_trips['transit_destination_time'])
df_matching_trips['car_destination_time'] = pd.to_datetime(df_matching_trips['car_destination_time'])

df_transit_trips = pd.read_csv(transit_trips_path)
df_transit_trips['date_time'] = pd.to_datetime(df_transit_trips['date_time'])

df_car_trips = pd.read_csv(car_trips_path)
df_car_trips['date_time'] = pd.to_datetime(df_car_trips['date_time'])

dict_transit_taxisharing = group_df_rows(df_matching_trips, 'transit_trip_id', '')
print len(dict_transit_taxisharing)
for transit_trip_id, list_integrations in dict_transit_taxisharing.iteritems():
    print transit_trip_id
    transit_trip = df_transit_trips[df_transit_trips['sampn_perno_tripno'] == transit_trip_id]
    dict_car_taxisharing = group_list_dict(list_integrations, 'car_trip_id')
    for car_trip_id, list_car_integrations in dict_car_taxisharing.iteritems():
        car_trip = df_car_trips[df_car_trips['sampn_perno_tripno'] == car_trip_id]
        print '\t',car_trip_id, len(list_car_integrations)
        for integration in list_car_integrations:
            transit_posisiton = transit_trip[(transit_trip['trip_sequence'] == integration['transit_trip_sequence'])\
            & (transit_trip['pos_sequence'] == integration['transit_pos_sequence'])]
            car_posisiton = car_trip[(car_trip['trip_sequence'] == integration['car_trip_sequence'])\
            & (car_trip['pos_sequence'] == integration['car_pos_sequence'])]

            print '\t\ttransit_origin:\t', transit_trip['date_time'].iloc[0]
            print '\t\tcar_origin:\t\t', car_trip['date_time'].iloc[0]
            print '\t\ttransit_integration:\t', transit_posisiton['date_time'].iloc[0]
            print '\t\tcar_integration:\t', car_posisiton['date_time'].iloc[0]
            print '\t\tstop_arrival:\t\t',integration['car_arrival_time_transit_stop']

            print '\t\ttransit_destination:\t', transit_trip['date_time'].iloc[-1]
            print '\t\ttransit_destination:\t', integration['transit_destination_time']
            print '\t\tcar_destination:\t', car_trip['date_time'].iloc[-1]
            print '\t\tcar_destination:\t', integration['car_destination_time']
            print '============================================='

            transit_saving_time = (transit_trip['date_time'].iloc[-1] - integration['transit_destination_time']).total_seconds()/60


            print transit_saving_time
            #break

    break

# select best car for each transit trip
