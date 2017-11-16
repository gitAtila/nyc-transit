'''
    Compute map routing through OSRM API
'''

import urllib2
import json
import math
from shapely.geometry import LineString

class OSRM_routing:

    def __init__(self, mode):
        self.url_head = 'http://router.project-osrm.org/route/v1/' + mode + '/'

    def street_routing_geometry(self, lon_origin, lat_origin, lon_destination, lat_destination):

        if math.isnan(lon_origin) or math.isnan(lon_destination):
            return {'duration': None, 'distance':None, 'geometry': None}

        url_tail = '?alternatives=false&steps=false&geometries=geojson'

        coordinates = str(lon_origin) + ',' + str(lat_origin)\
         + ';' + str(lon_destination) + ',' + str(lat_destination)

        url = self.url_head + coordinates + url_tail
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

            return {'duration': duration, 'distance':distance, 'geometry': geometry}

        return {'duration': None, 'distance':None, 'geometry': None}

    def street_routing_steps(self, lon_origin, lat_origin, lon_destination, lat_destination):

        if math.isnan(lon_origin) or math.isnan(lon_destination):
            return {'duration': None, 'distance':None, 'geometry': None}

        url_tail = '?alternatives=false&steps=true'

        coordinates = str(lon_origin) + ',' + str(lat_origin)\
         + ';' + str(lon_destination) + ',' + str(lat_destination)

        url = self.url_head + coordinates + url_tail
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
            distance = json_route['routes'][0]['distance']
            list_steps = json_route['routes'][0]['legs'][0]['steps']
            list_distance_duration_location = []
            list_distance_duration_location.append({'distance': 0,\
            'duration': 0, 'longitude': list_steps[0]['maneuver']['location'][0],\
            'latitude': list_steps[0]['maneuver']['location'][1]})
            total_distance = 0
            total_duration = 0
            for index in range(1,len(list_steps)):
                total_duration += list_steps[index-1]['duration']
                total_distance += list_steps[index-1]['distance']
                list_distance_duration_location.append({'distance': total_distance,\
                'duration': total_duration, 'longitude': list_steps[index]['maneuver']['location'][0],\
                'latitude': list_steps[index]['maneuver']['location'][1]})
            return list_distance_duration_location

        return []
