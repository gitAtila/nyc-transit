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

    def street_routing(self, lon_origin, lat_origin, lon_destination, lat_destination):

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
