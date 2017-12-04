'''
    Compute map routing through OpenTripPlanning API
'''

# start server
# java -Xmx2G -jar otp-1.2.0-shaded.jar --graphs /home/vod/amsj/remote_data/map/otp/graphs/ --router nyc --inMemory

import urllib2
import json
import math
import time
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
        'latitude': list_lon_lat_positions[0][1], 'distance': 0.0, 'stop_id': ''})

        total_distance = 0
        previous_datetime = origin_datetime
        for index in range(1,len(list_lon_lat_positions)):
            total_distance += list_distance[index-1]
            current_datetime = previous_datetime + timedelta(seconds=(list_distance[index-1]/average_speed))

            list_positions.append({'date_time': current_datetime, 'longitude': list_lon_lat_positions[index][0],\
            'latitude': list_lon_lat_positions[index][1], 'distance': total_distance, 'stop_id': ''})

            previous_datetime = current_datetime

        return list_positions

    def request_json(self, url):
        # print url
        json_response = {}
        try:
            opener = urllib2.build_opener()
            request = urllib2.Request(url, headers={'Content-Type': 'application/json'})
            response = opener.open(request)
            json_response = json.loads(response.read(request))
            opener.close()

        except urllib2.URLError:
            print 'URLError', url

        return json_response

    def subway_intemediate_stations(self, origin_datetime, tripId, from_stopId, to_stopId):
        list_positions = []

        url_stops = self.url_head + 'index/trips/' + tripId + '/stops/'
        url_stoptimes = self.url_head + 'index/trips/' + tripId + '/stoptimes/'

        json_stops = self.request_json(url_stops)
        json_stoptimes = self.request_json(url_stoptimes)

        first_stop = 0
        last_stop = len(json_stops)-1
        for position in range(len(json_stops)):
            if json_stops[position]['id'] == from_stopId:
                first_stop = position
            elif json_stops[position]['id'] == to_stopId:
                last_stop = position
                break
        json_stops = json_stops[first_stop:last_stop+1]
        json_stoptimes = json_stoptimes[first_stop:last_stop+1]

        #print origin_datetime.date()
        date = time.mktime(origin_datetime.date().timetuple())
        for index in range(len(json_stops)):
            one_day = timedelta(days=1).total_seconds()
            departure_time = json_stoptimes[index]['realtimeDeparture']
            nro_days = int(departure_time/one_day)

            departure_time = departure_time - nro_days*one_day
            date_time = datetime.fromtimestamp(date + departure_time)

            list_positions.append({'date_time': date_time, 'longitude': json_stops[index]['lon'],\
            'latitude': json_stops[index]['lat'], 'distance': '', 'stop_id': json_stops[index]['id']})

        return list_positions

    def route_positions(self, lat_origin, lon_origin, lat_destination, lon_destination, mode, date_time):

        route_position_times = []

        url_plan = self.url_head + 'plan?'
        if math.isnan(lon_origin) or math.isnan(lon_destination):
            return {'duration': None, 'distance':None, 'geometry': None}

        date = date_time.strftime('%m-%d-%Y')
        time = date_time.strftime('%I:%M%p')

        url_tail = '&mode=' + mode
        url_tail += '&arriveBy=false'
        url_tail += '&date=' + date
        url_tail += '&time=' + time

        coordinates = 'fromPlace=' + str(lat_origin) + ',' + str(lon_origin)\
         + '&toPlace=' + str(lat_destination) + ',' + str(lon_destination)

        url = url_plan + coordinates + url_tail
        # print url

        json_route = self.request_json(url)
        if 'plan' in json_route.keys():

            itinerary = json_route['plan']['itineraries'][0]
            # print itinerary.keys()

            difference_api_real = 0
            first_iteration = True
            trip_sequence = 1
            for leg in itinerary['legs']:

                list_positions = []
                # print 'mode:', leg['mode']

                origin_datetime = datetime.fromtimestamp(leg['startTime']/1000.0)
                destination_datetime = datetime.fromtimestamp(leg['endTime']/1000.0)

                # adapt timezone
                api_time = origin_datetime
                date_time = date + ' ' + time
                real_time = datetime.strptime(date_time, '%m-%d-%Y %I:%M%p')
                difference_api_real = (api_time - real_time).total_seconds()
                if difference_api_real >=  3600.0:
                    difference_api_real = int(difference_api_real/3600.0)
                else:
                    raise Exception('API timezone different from server')
                # print api_time, real_time, difference_api_real
                origin_datetime -= timedelta(hours=difference_api_real)
                destination_datetime -= timedelta(hours=difference_api_real)
                first_iteration = False

                if leg['mode'] == 'SUBWAY':

                    tripId = leg['tripId']
                    from_stopId = leg['from']['stopId']
                    to_stopId = leg['to']['stopId']
                    list_positions = self.subway_intemediate_stations(origin_datetime, tripId, from_stopId, to_stopId)

                elif leg['mode'] == 'WALK' or leg['mode'] == 'CAR':

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

                else:
                    raise Exception('mode dont known')

                pos_sequence = 1
                for position in list_positions:
                    position['pos_sequence'] = pos_sequence
                    position['trip_sequence'] = trip_sequence
                    route_position_times.append(position)
                    pos_sequence += 1
                    # print position['date_time']
                trip_sequence += 1
        else:
            print json_route['error']['message']
            print url
            return []
        return route_position_times


# otp = OTP_routing('nyc')
# otp.route_positions(40.71799, -74.00682,40.70290, -73.89439, 'SUBWAY,WALK', '11-30-2010', '1:00am')
# otp.subway_positions(40.71799, -74.00682,40.70290, -73.89439, '11-30-2017', '1:00am')
