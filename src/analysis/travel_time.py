'''
    Analyse the travel time of taxisharing routes
'''
from sys import argv
import pandas as pd

sbwy_individual_trip_path = argv[1]
taxi_individual_trip_path = argv[2]
sbwy_taxi_maching_path = argv[3]
taxisharing_trip_path = argv[4]

def group_df_rows(df, key_label):
    dict_grouped = dict()
    for index, row in df.iterrows():
        key = row[key_label]
        del row[key_label]
        dict_grouped.setdefault(key, []).append(row.to_dict())
    return dict_grouped

df_sbwy_individual_trip = pd.read_csv(sbwy_individual_trip_path)
df_taxi_individual_trip = pd.read_csv(taxi_individual_trip_path)
print df_sbwy_individual_trip

df_sbwy_taxi_matching = pd.read_csv(sbwy_taxi_maching_path)
dict_matching = group_df_rows(df_sbwy_taxi_matching, 'match_id')

df_taxisharing_trip = pd.read_csv(taxisharing_trip_path)

for match_id, match_route in dict_matching.iteritems():
    print match_id
    # select subway and taxi matching trips
    sbwy_matching_trip = [position for position in match_route if position['sequence'] < 7]
    taxi_matching_trip = [position for position in match_route if position['sequence'] >= 7]
    # sort sequence
    sbwy_matching_trip = sorted(sbwy_matching_trip, key=lambda position:position['sequence'])
    taxi_matching_trip = sorted(taxi_matching_trip, key=lambda position:position['sequence'])

    sbwy_trip_id = sbwy_matching_trip[0]['sampn_perno_tripno']

    sbwy_individual_trip = df_sbwy_individual_trip[df_sbwy_individual_trip['sampn_perno_tripno'] == sbwy_trip_id]
    #sbwy_individual_origin_time = sbwy_individual_trip['']

    # subway passenger time with taxisharing
    print 'sbwy_trip_id', sbwy_trip_id
    sbwy_taxisharing_origin_time = sbwy_matching_trip[0]['date_time']
    print sbwy_taxisharing_origin_time
    df_taxisharing_sbwy = df_taxisharing_trip[df_taxisharing_trip['sbwy_sampn_perno_tripno'] == sbwy_trip_id]
    for index, taxisharing_sbwy in df_taxisharing_sbwy.iterrows():
        sbwy_taxisharing_destination_time = taxisharing_sbwy['last_destination_time']
        if taxisharing_sbwy['sbwy_destination_first']:
            sbwy_taxisharing_destination_time = taxisharing_sbwy['first_destination_time']

        print '\t', sbwy_taxisharing_destination_time

    # taxi passenger time with taxisharing
    taxi_trip_id = taxi_matching_trip[0]['sampn_perno_tripno']
    print 'taxi_trip_id', taxi_trip_id
    taxi_taxisharing_origin_time = taxi_matching_trip[0]['date_time']
    print taxi_taxisharing_origin_time
    df_taxisharing_taxi = df_taxisharing_trip[df_taxisharing_trip['taxi_sampn_perno_tripno'] == taxi_trip_id]
    for index, taxisharing_taxi in df_taxisharing_taxi.iterrows():
        taxi_taxisharing_destination_time = taxisharing_taxi['first_destination_time']
        if taxisharing_taxi['sbwy_destination_first']:
            taxi_taxisharing_destination_time = taxisharing_taxi['last_destination_time']
        print '\t', taxi_taxisharing_destination_time
    break
