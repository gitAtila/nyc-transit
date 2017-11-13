'''
    get routes from positions of origin and destination
'''

from sys import argv
import pandas as pd
import urllib2
import json
import csv

from shapely.geometry import LineString
import geopandas as gpd

taxi_trip_path = argv[1]
result_path = argv[2]

url_head = 'http://router.project-osrm.org/route/v1/driving/'
url_tail = '?alternatives=false&steps=false&geometries=geojson'

df_taxi_trips = pd.read_csv(taxi_trip_path)

# file = open(result_path, 'wb')
# writer = csv.writer(file, quotechar = '"', quoting=csv.QUOTE_NONNUMERIC)
# writer.writerow(['sampn_perno_tripno', 'route'])
list_taxi_trip_route = []
for index, taxi_trip in df_taxi_trips.iterrows():

    coordinates = str(taxi_trip['lon_origin']) + ',' + str(taxi_trip['lat_origin'])\
     + ';' + str(taxi_trip['lon_destination']) + ',' + str(taxi_trip['lat_destination'])

    url = url_head + coordinates + url_tail
    print taxi_trip['sampn_perno_tripno']
    print url

    # request from APIs
    # try the url until succeed
    url_error = True
    while url_error == True:
        try:
            route = urllib2.urlopen(url)
            json_route = json.load(route)
            url_error = False

        except urllib2.URLError:
            print 'URLError', len(url)

    if json_route['code'] == 'Ok':
        #print taxi_trip['sampn_perno_tripno']
        geometry = LineString(json_route['routes'][0]['geometry']['coordinates'])
        duration = json_route['routes'][0]['duration']
        distance = json_route['routes'][0]['distance']
        # print duration
        # print distance
        # print geometry

        list_taxi_trip_route.append({'sampn_perno_tripno': taxi_trip['sampn_perno_tripno'],\
        'duration': duration, 'distance':distance, 'geometry': geometry})

    #break

gdf_taxi_trips = gpd.GeoDataFrame(list_taxi_trip_route, geometry='geometry')
print gdf_taxi_trips

gdf_taxi_trips.to_file(result_path)
