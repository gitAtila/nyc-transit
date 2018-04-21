'''
    Maximize transit passenger saving time alongside taxi passenger saving money
'''
from sys import argv, maxint
import pandas as pd

transit_private_trips_path = argv[1]
taxi_private_trips_path = argv[2]
temporal_spatial_match_path = argv[3]
cost_match_path = argv[4]
transit_factor = float(argv[5])
result_path = argv[6]

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

def merge_matches(df_temporal_spatial_match, df_cost_match):
    list_matches = []
    for index, costs in df_cost_match.iterrows():
        dict_match = df_temporal_spatial_match[(df_temporal_spatial_match['transit_id'] == costs['transit_id']) \
        & (df_temporal_spatial_match['stop_id'] == costs['stop_id']) \
        & (df_temporal_spatial_match['taxi_id'] == costs['taxi_id']) \
        & (df_temporal_spatial_match['taxi_pos_sequence'] == costs['taxi_pos_sequence'])].iloc[0].to_dict()
        dict_match['taxi_private_cost'] = costs['taxi_private_cost']
        dict_match['taxi_shared_cost'] = costs['taxi_shared_cost']
        dict_match['transit_shared_cost'] = costs['transit_shared_cost']
        list_matches.append(dict_match)

    return list_matches

def best_integration_possibility(df_matches, df_transit_private_trip, transit_factor):

    dict_transit_taxis = group_df_rows(df_matches, 'transit_id')
    dict_best_possibilities = dict()
    for transit_id, list_possibilities in dict_transit_taxis.iteritems():
        # print transit_id, len(list_possibilities)
        maximum_utility = -maxint
        best_stop_integration = ''
        for possibility in list_possibilities:
            df_original_transit = df_transit_private_trip[(df_transit_private_trip['sampn_perno_tripno'] == transit_id)]
            original_destination_time = df_original_transit['date_time'].iloc[-1]
            transit_saving_time = (original_destination_time - possibility['transit_destination_time']).total_seconds()
            taxi_saving_money = possibility['taxi_private_cost'] - possibility['taxi_shared_cost']

            # combine utilities
            integration_utility = (transit_saving_time * transit_factor) + (taxi_saving_money * (1-transit_factor))
            integration_utility2 = transit_saving_time * taxi_saving_money
            print integration_utility, integration_utility2

            # get the maximum utility
            if integration_utility > maximum_utility:
                maximum_utility = integration_utility
                possibility['transit_original_destination_time'] = original_destination_time
                dict_best_possibilities[transit_id] = possibility

    return dict_best_possibilities

df_cost_match = pd.read_csv(cost_match_path)

df_temporal_spatial_match = pd.read_csv(temporal_spatial_match_path)
df_temporal_spatial_match['taxi_arrival_time_transit_stop'] = pd.to_datetime(df_temporal_spatial_match['taxi_arrival_time_transit_stop'])
df_temporal_spatial_match['taxi_destination_time'] = pd.to_datetime(df_temporal_spatial_match['taxi_destination_time'])
df_temporal_spatial_match['transit_destination_time'] = pd.to_datetime(df_temporal_spatial_match['transit_destination_time'])

df_transit_private_trip = pd.read_csv(transit_private_trips_path)
df_transit_private_trip = df_transit_private_trip[df_transit_private_trip['sampn_perno_tripno']\
.isin(df_temporal_spatial_match['transit_id'].unique())]
df_transit_private_trip['date_time'] = pd.to_datetime(df_transit_private_trip['date_time'])
dict_transit_private_trip = group_df_rows(df_transit_private_trip, 'sampn_perno_tripno')

df_taxi_private_trip = pd.read_csv(taxi_private_trips_path)
df_taxi_private_trip = df_taxi_private_trip[df_taxi_private_trip['sampn_perno_tripno']\
.isin(df_temporal_spatial_match['taxi_id'].unique())]
df_taxi_private_trip['date_time'] = pd.to_datetime(df_taxi_private_trip['date_time'])
dict_taxi_private_trip = group_df_rows(df_taxi_private_trip, 'sampn_perno_tripno')

list_matches = merge_matches(df_temporal_spatial_match, df_cost_match)
df_matches = pd.DataFrame(list_matches)

dict_best_possibilities = best_integration_possibility(df_matches, df_transit_private_trip, transit_factor)

list_best_integration = []
for transit_id, dict_integration in dict_best_possibilities.iteritems():
    # print transit_id, dict_integration
    dict_integration['transit_id'] = transit_id
    list_best_integration.append(dict_integration)

df_best_integration = pd.DataFrame(list_best_integration)
df_best_integration = df_best_integration[['transit_id', 'stop_id', 'taxi_id', 'taxi_pos_sequence',\
'taxi_arrival_time_transit_stop', 'taxi_destination_time', 'transit_destination_time',\
'transit_original_destination_time','integration_distance', 'shared_distance', 'destinations_distance',\
'taxi_private_cost', 'taxi_shared_cost', 'transit_shared_cost']]
print df_best_integration

df_best_integration.to_csv(result_path, index=False)
