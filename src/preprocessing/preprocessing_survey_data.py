'''
    Read survey dataset, put times and positions in a correct format and select interested fields
'''
from sys import argv
import pandas as pd
import math
import geopandas as gpd
from datetime import datetime

survey_data_path = argv[1]
shapefile_census_tract_path = argv[2]
result_path = argv[3]

# read survey data
df_survey_data = pd.read_csv(survey_data_path)
# read census tract data
gdf_census_tract = gpd.read_file(shapefile_census_tract_path)

# select interested fields
df_survey_data = df_survey_data[['sampn', 'perno', 'tripno', 'trip_sdate', 'trip_edate',\
 'dtime', 'atime', 'O_TRACT', 'O_Boro', 'O_COUNTY', 'D_TRACT', 'D_Boro', 'D_COUNTY',\
 'MODE_G10', 'NSUB', 'StopAreaNo']]

def format_origin_destination_datetime(date_origin, time_origin, date_destination, time_destination):
    date_time_origin = None
    date_time_destination = None
    try:
        date_origin = date_origin.split(' ')[0]
        date_destination = date_destination.split(' ')[0]
        date_time_origin = datetime.strptime(date_origin + ' ' + time_origin, '%m/%d/%y %H:%M')
        date_time_destination = datetime.strptime(date_destination + ' ' + time_destination, '%m/%d/%y %H:%M')

    except ValueError:

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

    return date_time_origin, date_time_destination

def float_to_int_str(float_number):
	return str(float_number).split('.')[0]

def census_tract_centroid(gdf_census_tract, ct_id_key, ct_borough_id_key,\
sv_tract_id, sv_county_id, sv_borough_id):

    if math.isnan(sv_borough_id) or sv_borough_id > 5:
        return gpd.GeoSeries()

    borough_survey_shape = {1:'1', 2:'4', 3:'2', 4:'3', 5:'5'}

    census_tract_id = float_to_int_str(sv_tract_id)
    census_tract_id = census_tract_id[len(float_to_int_str(sv_county_id)):]

    gdf_boroughs_cd_id = gdf_census_tract[gdf_census_tract[ct_id_key] == census_tract_id]

    ct_polygon = gdf_boroughs_cd_id[gdf_boroughs_cd_id[ct_borough_id_key] == borough_survey_shape[sv_borough_id]]
    polygon_centroid = ct_polygon.centroid
    return polygon_centroid

# format datetime of origin and destination
list_survey_data = []
for index, trip in df_survey_data.iterrows():
    #print trip
    dict_trip = trip.to_dict()

    date_time_origin, date_time_destination = format_origin_destination_datetime(trip['trip_sdate'],\
    trip['dtime'], trip['trip_edate'], trip['atime'])

    dict_trip['date_time_origin'] = date_time_origin
    dict_trip['date_time_destination'] = date_time_destination

    origin_position = census_tract_centroid(gdf_census_tract, 'ct2010', 'boro_code',\
    trip['O_TRACT'], trip['O_COUNTY'], trip['O_Boro'])

    destination_position = census_tract_centroid(gdf_census_tract, 'ct2010', 'boro_code',\
    trip['D_TRACT'], trip['D_COUNTY'], trip['D_Boro'])

    if len(origin_position) == 1:
        #print 'origin_position', origin_position
        dict_trip['lon_origin'] = float(origin_position.x)
        dict_trip['lat_origin'] = float(origin_position.y)
    else:
        #print 'origin_position', 'none'
        dict_trip['lon_origin'] = None
        dict_trip['lat_origin'] = None

    if len(destination_position) == 1:
        #print 'destination_position', destination_position
        dict_trip['lon_destination'] = float(destination_position.x)
        dict_trip['lat_destination'] = float(destination_position.y)
    else:
        #print 'destination_position', 'none'
        dict_trip['lon_destination'] = None
        dict_trip['lat_destination'] = None

    list_survey_data.append(dict_trip)

df_trip_position_time = pd.DataFrame(list_survey_data)
df_trip_position_time = df_trip_position_time[['sampn', 'perno', 'tripno', 'MODE_G10', 'NSUB', 'StopAreaNo',\
'date_time_origin', 'lon_origin', 'lat_origin','date_time_destination', 'lon_destination', 'lat_destination']]
df_trip_position_time.to_csv(result_path, index_label='id')
