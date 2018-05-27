'''
    Evaluate costs of temporal spatial matches
'''
from sys import argv
import pandas as pd
from datetime import datetime

transit_private_trips_path = argv[1]
taxi_private_trips_path = argv[2]
temporal_spatial_match_path = argv[3]
# transit_initial_cost_parcel = float(argv[4])
# transit_integration_cost_parcel = float(argv[5])
# transit_shared_cost_parcel = float(argv[6])
# result_path = argv[4]
detour_factor_path = argv[4]
integration_costs_path = argv[5]


def nyc_taxi_cost(date_time_origin, trip_distance_meters, stopped_duration_sec):

    # costs in dolar
    initial_charge = 2.5
    tax_per_ride = 0.5
    rate_per_mile = 2.5 # 50 cents per 1/5 mile
    rate_per_minute_stopped = 0.4 # per minute
    peak_hour_surcharge = 1 # Mon - Fri 4pm to 8pm
    night_surcharge = 0.5 # 8pm to 6am

    peak_weekdays = range(0, 5) # Mon - Fri
    peak_hours = range(16, 20) # 4pm to 8pm
    night_hours = range(20, 24) + range(0,7) # 8pm to 6am

    mile_in_meters = 0.000621371

    # airport
    # surcharge_to_newark = 15
    # jfk_manhattan = 45

    ride_cost = initial_charge + tax_per_ride
    # peak hours
    if date_time_origin.weekday() in peak_weekdays and date_time_origin.hour in peak_hours:
        ride_cost += peak_hour_surcharge

    # night
    if date_time_origin.hour in night_hours:
        ride_cost += night_surcharge

    # distance
    price_per_meter = mile_in_meters * rate_per_mile
    ride_cost += price_per_meter * trip_distance_meters

    # stopped duration
    ride_cost += (stopped_duration_sec/60) * rate_per_minute_stopped

    return ride_cost

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

def compute_integration_costs(dict_transit_private_trip, dict_taxi_private_trip, df_matches):

    list_integration_costs = []

    for index, matching in df_matches.iterrows():
        list_detour_factor = []
        list_transit_trip = dict_transit_private_trip[matching['transit_id']]
        list_taxi_private_trip = dict_taxi_private_trip[matching['taxi_id']]

        taxi_private_cost = nyc_taxi_cost(list_taxi_private_trip[0]['date_time'], list_taxi_private_trip[-1]['distance'], 0)

        taxi_acceptance_position = [position for position in list_taxi_private_trip\
        if position['pos_sequence'] == matching['taxi_pos_sequence']][0]

        # print matching['stop_id']
        # for position in list_transit_trip:
        #     print position['mode'], position['stop_id']

        transit_stop_position = [position for position in list_transit_trip\
        if position['stop_id'] == matching['stop_id']][0]

        # verify if it is a valid matching
        if transit_stop_position['date_time'] < matching['transit_destination_time']\
        and transit_stop_position['date_time'] < matching['taxi_destination_time']\
        and matching['taxi_arrival_time_transit_stop'] < matching['transit_destination_time']\
        and matching['taxi_arrival_time_transit_stop'] < matching['taxi_destination_time']:

            sharing_duration = (matching['taxi_destination_time'] - list_taxi_private_trip[0]['date_time']).total_seconds()
            private_duration = (list_taxi_private_trip[-1]['date_time'] - list_taxi_private_trip[0]['date_time']).total_seconds()

            taxi_time_relative_detour = (sharing_duration - private_duration)/private_duration
            detour_factor = 1/taxi_time_relative_detour

            list_detour_factor.append({'transit_id':matching['transit_id'], 'taxi_id':matching['taxi_id'],\
            'detour_factor':detour_factor})

            integration_stopped_time = 0
            if transit_stop_position['date_time'] > matching['taxi_arrival_time_transit_stop']:
                integration_stopped_time = (transit_stop_position['date_time'] - matching['taxi_arrival_time_transit_stop']).total_seconds()

            transit_destination_first = False
            if matching['transit_destination_time'] < matching['taxi_destination_time']:
                transit_destination_first = True

            taxi_shared_cost = nyc_taxi_cost(list_taxi_private_trip[0]['date_time'], \
            (taxi_acceptance_position['distance'] + matching['destinations_distance']\
            + matching['integration_distance'] + matching['shared_distance']), integration_stopped_time)

            transit_shared_cost = taxi_shared_cost * detour_factor
            taxi_shared_cost = taxi_shared_cost * (1 - detour_factor)

            # taxi passenger save money
            if taxi_shared_cost < taxi_private_cost:
                list_integration_costs.append({'transit_id': matching['transit_id'], 'stop_id': matching['stop_id'],\
                'taxi_id': matching['taxi_id'], 'taxi_pos_sequence': matching['taxi_pos_sequence'],\
                'taxi_private_cost': taxi_private_cost, 'taxi_shared_cost': taxi_shared_cost,\
                'transit_shared_cost': transit_shared_cost})

    return list_integration_costs, list_detour_factor

# read matches
df_matches = pd.read_csv(temporal_spatial_match_path)
df_matches['taxi_arrival_time_transit_stop'] = pd.to_datetime(df_matches['taxi_arrival_time_transit_stop'])
df_matches['taxi_destination_time'] = pd.to_datetime(df_matches['taxi_destination_time'])
df_matches['transit_destination_time'] = pd.to_datetime(df_matches['transit_destination_time'])

# read transit private route
df_transit_private_trip = pd.read_csv(transit_private_trips_path)
df_transit_private_trip = df_transit_private_trip[df_transit_private_trip['sampn_perno_tripno'].isin(df_matches['transit_id'].unique())]
df_transit_private_trip['date_time'] = pd.to_datetime(df_transit_private_trip['date_time'])
dict_transit_private_trip = group_df_rows(df_transit_private_trip, 'sampn_perno_tripno')

# read taxi private route
df_taxi_private_trip = pd.read_csv(taxi_private_trips_path)
df_taxi_private_trip = df_taxi_private_trip[df_taxi_private_trip['sampn_perno_tripno'].isin(df_matches['taxi_id'].unique())]
df_taxi_private_trip['date_time'] = pd.to_datetime(df_taxi_private_trip['date_time'])
dict_taxi_private_trip = group_df_rows(df_taxi_private_trip, 'sampn_perno_tripno')

# compute and compare costs
list_integration_costs, list_detour_factor = compute_integration_costs(dict_transit_private_trip,\
dict_taxi_private_trip, df_matches)

# save
df_detour_factor = pd.DataFrame(list_detour_factor)
df_detour_factor = df_detour_factor[['transit_id', 'taxi_id', 'detour_factor']]
df_detour_factor.to_csv(detour_factor_path,index=False)

df_integration_costs = pd.DataFrame(list_integration_costs)
df_integration_costs = df_integration_costs[['transit_id', 'stop_id', 'taxi_id', 'taxi_pos_sequence',\
'taxi_private_cost', 'taxi_shared_cost', 'transit_shared_cost']]
print df_integration_costs
df_integration_costs.to_csv(integration_costs_path, index=False)
