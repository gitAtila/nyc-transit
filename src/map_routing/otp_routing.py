'''
    Compute map routing through OpenTripPlanning API
'''
# start server
# java -Xmx2G -jar otp-1.2.0-shaded.jar --graphs /home/vod/amsj/remote_data/map/otp/graphs/ --router nyc --inMemory
import urllib2
import json
import math
from shapely.geometry import LineString
import polyline

class OTP_routing:

    def __init__(self, routerId):
        self.url_head = 'http://localhost:8080/otp/routers/' + routerId + '/'

    def street_routing_geometry(self, lat_origin, lon_origin, lat_destination, lon_destination, mode):
        self.url_head += 'plan?'
        if math.isnan(lon_origin) or math.isnan(lon_destination):
            return {'duration': None, 'distance':None, 'geometry': None}

        url_tail = '?mode='+mode

        coordinates = 'fromPlace=' + str(lat_origin) + ',' + str(lon_origin)\
         + '&toPlace=' + str(lat_destination) + ',' + str(lon_destination)

        url = self.url_head + coordinates + url_tail
        print url

        # request from APIs
        # try the url until succeed
        url_error = True
        #while url_error == True:
        try:
            opener = urllib2.build_opener()
            request = urllib2.Request(url, headers={'Content-Type': 'application/json'})
            response = opener.open(request)
            json_respone = json.loads(response.read(request))

            # print json_respone
            #print route
            url_error = False

        except urllib2.URLError:
            print 'URLError', len(url)

        print json_respone.keys()
        print json_respone['plan'].keys()
        for itinerary in json_respone['plan']['itineraries']:
            print itinerary.keys()
            for leg in itinerary['legs']:
                print leg['mode']
                print leg.keys()
                if leg['mode'] == 'SUBWAY':
                    print leg['tripId']
                    print leg['from']['stop']
                    print leg['to']
                print leg['legGeometry']
                print polyline.decode(leg['legGeometry']['points'])
                print ''

                #break
            break
        # if json_route['code'] == 'Ok':
        #     #print taxi_trip['sampn_perno_tripno']
        #     geometry = LineString(json_route['routes'][0]['geometry']['coordinates'])
        #     duration = json_route['routes'][0]['duration']
        #     distance = json_route['routes'][0]['distance']
        #
        #     return {'duration': duration, 'distance':distance, 'geometry': geometry}
        #
        # return {'duration': None, 'distance':None, 'geometry': None}

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

otp = OTP_routing('nyc')
otp.street_routing_geometry(40.730542,-73.994,40.747029,-73.993742, 'TRANSIT')
