'''
    Compute map routing through OpenTripPlanning API
'''

# start server
# java -Xmx2G -jar otp-1.2.0-shaded.jar --graphs /home/vod/amsj/remote_data/map/otp/graphs/ --router nyc --inMemory

import urllib2
import json
import math
from datetime import datetime, timedelta
from shapely.geometry import LineString
import polyline

class OTP_routing:

    def __init__(self, routerId):
        self.url_head = 'http://localhost:8080/otp/routers/' + routerId + '/'

    def walking_intermediate_times(self, origin_datetime, destination_datetime, list_distance,\
    list_lon_lat_positions, average_speed):
        list_positions = []

        list_positions.append({'date_time': origin_datetime, 'longitude': list_lon_lat_positions[0][0],\
        'latitude': list_lon_lat_positions[0][1], 'distance': 0.0})

        total_distance = 0
        previous_datetime = origin_datetime
        for index in range(1,len(list_lon_lat_positions)):
            total_distance += list_distance[index-1]
            current_datetime = previous_datetime + timedelta(seconds=(list_distance[index-1]/average_speed))

            list_positions.append({'date_time': current_datetime, 'longitude': list_lon_lat_positions[index][0],\
            'latitude': list_lon_lat_positions[index][1], 'distance': total_distance})

            previous_datetime = current_datetime

        return list_positions

    def subway_intemediate_stations(self, origin_datetime, tripId, from_stopId, to_stopId):

        url = self.url_head + 'index/trips/' + tripId + '/stops/'
        print url

        try:
            opener = urllib2.build_opener()
            request = urllib2.Request(url, headers={'Content-Type': 'application/json'})
            response = opener.open(request)
            json_respone = json.loads(response.read(request))
            opener.close()

            first_stop = 0
            last_stop = len(json_respone)-1
            for position in range(len(json_respone)):
                if json_respone[position]['id'] == from_stopId:
                    first_stop = position
                elif json_respone[position]['id'] == to_stopId:
                    last_stop = position
                    break
            print first_stop, last_stop


            for stop in json_respone:
                print stop

        except urllib2.URLError:
            print 'URLError', len(url)



        list_positions = []

    def street_routing_geometry(self, lat_origin, lon_origin, lat_destination, lon_destination, mode, date, time):
        url_plan = self.url_head + 'plan?'
        if math.isnan(lon_origin) or math.isnan(lon_destination):
            return {'duration': None, 'distance':None, 'geometry': None}

        url_tail = '&mode=' + mode
        url_tail += '&arriveBy=false'
        url_tail += '&date=' + date
        url_tail += '&time=' + time

        coordinates = 'fromPlace=' + str(lat_origin) + ',' + str(lon_origin)\
         + '&toPlace=' + str(lat_destination) + ',' + str(lon_destination)

        url = url_plan + coordinates + url_tail
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
            opener.close()
            url_error = False

        except urllib2.URLError:
            print 'URLError', len(url)

        print json_respone.keys()
        print json_respone['plan'].keys()
        for itinerary in json_respone['plan']['itineraries']:
            print itinerary.keys()
            for leg in itinerary['legs']:
                print 'mode:', leg['mode']
                print leg.keys()
                print 'origin_datetime:', datetime.fromtimestamp(leg['startTime']/1000.0) - timedelta(hours=3)
                origin_datetime = datetime.fromtimestamp(leg['startTime']/1000.0) - timedelta(hours=3)
                print 'destination_datetime:', datetime.fromtimestamp(leg['endTime']/1000.0) - timedelta(hours=3)

                if leg['mode'] == 'SUBWAY':

                    #print 'from-lon-lat:', leg['from']['lon'], leg['from']['lat']
                    print 'tripId:', leg['tripId']
                    tripId = leg['tripId']
                    print 'from-stopId:', leg['from']['stopId']
                    from_stopId = leg['from']['stopId']
                    #print 'from-lon-lat:', leg['from']['lon'], leg['from']['lat']
                    print 'to-stopId:', leg['to']['stopId']
                    to_stopId = leg['to']['stopId']
                    #print 'to-lon-lat:', leg['to']['lon'], leg['to']['lon']
                    print 'distance:', leg['distance']
                    self.subway_intemediate_stations(origin_datetime, tripId, from_stopId, to_stopId)

                elif leg['mode'] == 'WALK':

                    origin_datetime = datetime.fromtimestamp(leg['startTime']/1000.0) - timedelta(hours=3)
                    destination_datetime = datetime.fromtimestamp(leg['endTime']/1000.0) - timedelta(hours=3)

                    origin_position = (leg['from']['lon'], leg['from']['lat'])
                    destination_position = (leg['to']['lon'], leg['to']['lat'])

                    total_distance = leg['distance']
                    total_duration = (destination_datetime - origin_datetime).total_seconds()
                    average_speed = total_distance/total_duration

                    list_distance = []
                    list_lon_lat_positions = []
                    #list_lon_lat_positions.append(origin_position)
                    for step in leg['steps']:
                        list_distance.append(step['distance'])
                        list_lon_lat_positions.append((step['lon'], step['lat']))
                    list_lon_lat_positions.append(destination_position)

                    list_positions = self.walking_intermediate_times(origin_datetime, destination_datetime,\
                    list_distance, list_lon_lat_positions, average_speed)
                    for position in list_positions:
                        print position

                # print leg['legGeometry']
                #print polyline.decode(leg['legGeometry']['points'])
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
otp.street_routing_geometry(40.71799, -74.00682,40.70290, -73.89439, 'TRANSIT,WALK', '11-30-2017', '1:00am')
