'''
    Analyse estimatives of time from transit car matching
'''

from sys import argv, maxint
import pandas as pd

from otp_routing import OTP_routing

transit_trips_path = argv[1]
car_trips_path = argv[2]
matching_trips_path = argv[3]
router_id = argv[4]
result_file = argv[5]

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

def list_best_integrations(df_transit_trips, df_car_trips, dict_transit_taxisharing):

    list_best_integrations = []
    for transit_trip_id, list_integrations in dict_transit_taxisharing.iteritems():

        transit_trip = df_transit_trips[df_transit_trips['sampn_perno_tripno'] == transit_trip_id]
        dict_car_taxisharing = group_list_dict(list_integrations, 'car_trip_id')
        # print '\n', transit_trip_id, len(dict_car_taxisharing)

        best_car_saving_time = -maxint
        best_car_integration_position = {}
        for car_trip_id, list_car_integrations in dict_car_taxisharing.iteritems():
            car_trip = df_car_trips[df_car_trips['sampn_perno_tripno'] == car_trip_id]
            # print '\t',car_trip_id, len(list_car_integrations)

            max_saving_time = -maxint
            best_integration_position = {}
            for integration in list_car_integrations:
                transit_saving_time = (transit_trip['date_time'].iloc[-1] - integration['transit_destination_time']).total_seconds()

                if transit_saving_time > max_saving_time:
                    max_saving_time = transit_saving_time
                    integration['transit_trip_id'] = transit_trip_id
                    integration['car_trip_id'] = car_trip_id
                    best_integration_position = integration

            if max_saving_time > best_car_saving_time:
                best_car_saving_time = max_saving_time
                best_car_integration_position = best_integration_position

        list_best_integrations.append(best_car_integration_position)

    return list_best_integrations

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

list_best_integrations = list_best_integrations(df_transit_trips, df_car_trips, dict_transit_taxisharing)

otp = OTP_routing(router_id)

list_passengers_trip = []
for integration in list_best_integrations:
    print integration['transit_trip_id'], integration['car_trip_id']

    transit_trip = df_transit_trips[df_transit_trips['sampn_perno_tripno'] == integration['transit_trip_id']]
    transit_integration_position = transit_trip[(transit_trip['trip_sequence'] == integration['transit_trip_sequence'])\
    & (transit_trip['pos_sequence'] == integration['transit_pos_sequence'])].iloc[0].T.to_dict()
    transit_destination_position = transit_trip.iloc[-1].T.to_dict()

    # print transit_integration_position
    # print transit_destination_position

    passenger_otp_trip = otp.route_positions(transit_integration_position['latitude'],\
    transit_integration_position['longitude'],\
    transit_destination_position['latitude'], transit_destination_position['longitude'],\
    'CAR', transit_integration_position['date_time'])

    for passenger_trip in passenger_otp_trip:

        if len(passenger_trip) > 0:
            passenger_trip['transit_trip_id'] = integration['transit_trip_id']
            passenger_trip['car_trip_id'] = integration['car_trip_id']
            list_passengers_trip.append(passenger_trip)

df_passenger_trip = pd.DataFrame(list_passengers_trip)
df_passenger_trip = df_passenger_trip[['transit_trip_id', 'car_trip_id', 'trip_sequence',\
'pos_sequence','date_time', 'longitude', 'latitude', 'distance', 'stop_id']]
print df_passenger_trip
df_passenger_trip.to_csv(result_file, index=False)
    # break

# plot_cdf_two_curves(list_taxi_saving_money, list_transit_extra_cost, 'taxi saving money', 'transit extra cost', 'dollars', chart_path)
