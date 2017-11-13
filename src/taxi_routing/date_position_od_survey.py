from sys import argv
from datetime import datetime
import pandas as pd
import numpy as np
import geopandas as gpd

travel_survey_data_path = argv[1]
shapefile_census_tract_base_path = argv[2]
result_path = argv[3]

def float_to_int_str(float_number):
	return str(float_number).split('.')[0]

def get_origin_destination_tract_id(s_trip):
	o_tract_id = float_to_int_str(s_trip['O_TRACT'])
	o_tract_id = o_tract_id[len(float_to_int_str(s_trip['O_COUNTY'])):]

	d_tract_id = float_to_int_str(s_trip['D_TRACT'])
	d_tract_id = d_tract_id[len(float_to_int_str(s_trip['D_COUNTY'])):]

	return {'o_tract_id': o_tract_id, 'd_tract_id': d_tract_id}

def get_taxi_trips_in_nyc(df_trips, gdf_census_tract):
	# filter taxi trips
	df_taxi_trips = df_trips[df_trips['MODE_G10'] == 7]

	list_trips_in_nyc = []
	tract_id_nyc = gdf_census_tract['ct2010'].tolist()
	for index, trip in df_taxi_trips.iterrows():
		od_tract = get_origin_destination_tract_id(trip)
		if od_tract['o_tract_id'] in tract_id_nyc and od_tract['d_tract_id'] in tract_id_nyc:
			list_trips_in_nyc.append(trip)

	print 'list_trips_in_nyc', len(list_trips_in_nyc)
	return pd.DataFrame(list_trips_in_nyc)

def taxi_trip_time_position(travel_survey_data_path, shapefile_census_tract_base_path):
    list_taxi_trips = []

    # read and filter taxi trips in nyc
    df_trips = pd.read_csv(travel_survey_data_path)
    gdf_census_tract = gpd.read_file(shapefile_census_tract_base_path)
    df_taxi_service_trips = get_taxi_trips_in_nyc(df_trips, gdf_census_tract)
    del df_trips

    # census tracts of origin and destination should be different
    df_taxi_service_trips = df_taxi_service_trips[df_taxi_service_trips['O_TRACT'] != df_taxi_service_trips['D_TRACT']]

    borough_survey_shape = {1:'1', 2:'4', 3:'2', 4:'3', 5:'5'}

    for index, taxi_trip in df_taxi_service_trips.iterrows():
        # get interested variables
        sampn_perno_tripno = str(taxi_trip['sampn']) + '_' + str(taxi_trip['perno']) + '_' + str(taxi_trip['tripno'])
        print 'sampn_perno_tripno', sampn_perno_tripno

        borough_origin = taxi_trip['O_Boro']
        borough_destination = taxi_trip['D_Boro']

        print 'boro_origin', borough_origin
        print 'boro_destination', borough_destination

        if borough_origin == 6 or borough_destination == 6:
            print 'Error: Origin or destination location out of city.'
            print ''
        elif np.isnan(borough_origin) or np.isnan(borough_destination):
            print 'Error: Origin or destination is not known.'
            print ''
        else:
            # get census tract code from survey
            ct_od = get_origin_destination_tract_id(taxi_trip)
            ct_origin = ct_od['o_tract_id']
            ct_destination = ct_od['d_tract_id']

            print 'ct_origin', ct_origin
            print 'ct_destination', ct_destination

            date_origin = taxi_trip['trip_sdate'].split(' ')[0]
            date_destination = taxi_trip['trip_edate'].split(' ')[0]
            time_origin = taxi_trip['dtime']
            time_destination = taxi_trip['atime']
            try:
                date_time_origin = datetime.strptime(date_origin + ' ' + time_origin, '%m/%d/%y %H:%M')
                date_time_destination = datetime.strptime(date_destination + ' ' + time_destination, '%m/%d/%y %H:%M')

                print 'date_time_origin', date_time_origin
                print 'date_time_destination', date_time_destination
            except ValueError:

                print 'Date error'
                print '"'+ date_origin +'"'+ time_origin +'"'
                print '"'+ date_destination +'"'+ time_destination +'"'

                destination_hour = time_destination.split(':')[0]
                if time_origin == '99:99' and (destination_hour == '01' or destination_hour == '00'):
                    time_origin = '00:00'
                    date_time_origin = datetime.strptime(date_origin + ' ' + time_origin, '%m/%d/%y %H:%M')
                    date_time_destination = datetime.strptime(date_destination + ' ' + time_destination, '%m/%d/%y %H:%M')

                origin_hour = time_origin.split(':')[0]
                if time_destination == '99:99' and origin_hour == '23':
                    time_destination = '00:00'
                    date_time_origin = datetime.strptime(date_origin + ' ' + time_origin, '%m/%d/%y %H:%M')
                    date_time_destination = datetime.strptime(date_destination + ' ' + time_destination, '%m/%d/%y %H:%M')

                print 'date_time_origin', date_time_origin
                print 'date_time_destination', date_time_destination

            gdf_ct_origin = gdf_census_tract[gdf_census_tract['ct2010'] == ct_origin]
            gs_ct_origin = gdf_ct_origin[gdf_ct_origin['boro_code'] == borough_survey_shape[borough_origin]]
            origin_centroid = gs_ct_origin.centroid

            gdf_ct_destination = gdf_census_tract[gdf_census_tract['ct2010'] == ct_destination]
            gs_ct_destination = gdf_ct_destination[gdf_ct_destination['boro_code'] == borough_survey_shape[borough_destination]]
            destination_centroid = gs_ct_destination.centroid

            if len(origin_centroid) == 0 or len(destination_centroid) == 0:
                print 'Error: Unable to get both positions of origin and destination.'
                print ''
            else:
                print 'origin_centroid', origin_centroid
                print 'destination_centroid', destination_centroid
                print ''
                list_taxi_trips.append({'sampn_perno_tripno': sampn_perno_tripno, 'date_time_origin': date_time_origin,\
                'date_time_destination': date_time_destination, 'lon_origin': float(origin_centroid.x),\
                'lat_origin': float(origin_centroid.y), 'lon_destination': float(destination_centroid.x),\
                'lat_destination': float(destination_centroid.y)})

    return pd.DataFrame(list_taxi_trips)

df_taxi_trips = taxi_trip_time_position(travel_survey_data_path, shapefile_census_tract_base_path)
df_taxi_trips = df_taxi_trips[['sampn_perno_tripno', 'date_time_origin', 'lon_origin', 'lat_origin',\
'date_time_destination', 'lon_destination', 'lat_destination']]

df_taxi_trips.to_csv(result_path, index_label='id')
print df_taxi_trips
