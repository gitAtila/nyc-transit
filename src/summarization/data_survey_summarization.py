# read and processing bus data survey
from sys import argv
import pandas as pd
import numpy as np
from datetime import datetime
import csv

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.colors import rgb2hex, Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.colorbar import ColorbarBase

import shapefile
from shapely.geometry import Polygon
from descartes.patch import PolygonPatch

import geopandas as gpd
from geopandas.tools import sjoin

from statsmodels.distributions.empirical_distribution import ECDF

travel_survey_file_wkdy = argv[1]
travel_survey_file_sat = argv[2]
travel_survey_file_sun = argv[3]
shp_puma = argv[4]
# shp_subway_stations = argv[5]
chart_path = argv[5]

# shapefile_census_tract = argv[4]
# shapefile_borough = argv[6]

def list_from_csv(travel_survey_file):
	list_trip_data = []
	with open(travel_survey_file, 'rb') as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
		headings = next(csv_reader)

		for row in csv_reader:
			list_trip_data.append(dict(zip(headings, row)))
			#break
	return list_trip_data

def df_from_csv(travel_survey_file):
	return pd.read_csv(travel_survey_file)

def df_normaliser(df):
	return df.T.div(df.sum(axis=0), axis=0).T

def ecdf_df(df, column_name):
	list_column = df[column_name].tolist()
	list_column.sort()
	return ECDF(list_column)
# total departure and arrival time by hour
def total_departure_arrival_trips(df_trips, chart_name):

	df_trips_subway = df_trips[df_trips['MODE_G8'] == 1]
	df_trips_subway_bus = df_trips[df_trips['MODE_G8'] == 2]
	df_trips_bus = df_trips[df_trips['MODE_G8'] == 3]
	df_trips_taxi = df_trips[df_trips['MODE_G8'] == 5]

	departure_subway = df_trips_subway.groupby('HR_DEP')['TRIP_ID'].count()
	departure_subway_bus = df_trips_subway_bus.groupby('HR_DEP')['TRIP_ID'].count()
	departure_bus = df_trips_bus.groupby('HR_DEP')['TRIP_ID'].count()
	departure_taxi = df_trips_taxi.groupby('HR_DEP')['TRIP_ID'].count()

	# arrival_count = df_trips.groupby('HR_ARR')['TRIP_ID'].count()
	# 'NYC Subway', 'Subway + Bus', 'NY-MTA Bus (only)', 'Other Transit', 'Taxi, Car/Van'
	df_total_grouped_hour = pd.concat([departure_subway.rename('NYC Transit'),\
	departure_subway_bus.rename('Subway + Bus'), departure_bus.rename('NY-MTA Bus (only)'),\
	departure_taxi.rename('Taxi, Car/Van Service')], axis=1)

	df_total_grouped_hour = df_total_grouped_hour.drop(99)

	print df_total_grouped_hour
	df_total_grouped_hour = df_normaliser(df_total_grouped_hour)

	print df_total_grouped_hour
	ax = df_total_grouped_hour.plot()
	ax.xaxis.set_major_locator(ticker.MultipleLocator(3)) # set x sticks interal
	ax.set_xlabel('Hour')
	ax.set_ylabel('% of Trips')
	plt.tight_layout()
	fig = ax.get_figure()
	fig.savefig(chart_name)

	# print df_trips_subway['HR_DEP']
	#
	# df_trips_subway = df_trips_subway[df_trips_subway['HR_DEP'] != 99]
	# df_trips_subway_bus = df_trips_subway_bus[df_trips_subway_bus['HR_DEP'] != 99]
	# df_trips_bus = df_trips_bus[df_trips_bus['HR_DEP'] != 99]
	# df_trips_taxi = df_trips_taxi[df_trips_taxi['HR_DEP'] != 99]
	#
	# ecdf_subway = ecdf_df(df_trips_subway, 'HR_DEP')
	# ecdf_subway_bus = ecdf_df(df_trips_subway_bus, 'HR_DEP')
	# ecdf_bus = ecdf_df(df_trips_bus, 'HR_DEP')
	# ecdf_taxi = ecdf_df(df_trips_taxi, 'HR_DEP')
	#
	# fig, ax = plt.subplots()
	# plt.plot(ecdf_subway.x, ecdf_subway.y, label='NYC Subway')
	# plt.plot(ecdf_subway_bus.x, ecdf_subway_bus.y, label='Subway + Bus')
	# plt.plot(ecdf_bus.x, ecdf_bus.y, label='NY-MTA Bus (only)')
	# plt.plot(ecdf_taxi.x, ecdf_taxi.y, label='Taxi, Car/Van')
	#
	# # ax.xaxis.set_major_locator(ticker.MultipleLocator(60)) # set x sticks interal
	# plt.grid()
	# plt.legend()
	# ax.set_title('ECDF Departure Time')
	# plt.tight_layout()
	# fig.savefig(chart_name)

# # transit and no transit mode
#print df_trips.groupby('MODE_G2')['TRIP_ID'].count()

# # modes
def travels_per_mode(df_trips_wkdy, df_trips_sat, df_trips_sun, chart_name):
	print 'test'

	df_trips = pd.concat([df_trips_wkdy, df_trips_sat, df_trips_sun])
	s_mode_count = df_trips.groupby('MODE_G10')['TRIP_ID'].count()
	# print s_mode_count
	#
	# s_mode_count_wkdy = df_trips_wkdy.groupby('MODE_G10')['TRIP_ID'].count()
	# s_mode_count_sat = df_trips_sat.groupby('MODE_G10')['TRIP_ID'].count()
	# s_mode_count_sun = df_trips_sun.groupby('MODE_G10')['TRIP_ID'].count()

	s_mode_name = pd.Series(['NYC Subway Only', 'NYC Subway + Bus', 'NY or MTA Bus (no sub)', 'Commuter Rail (no nyct)', 'Other Rail (no nyct)',\
	 'Other Transit (no nyct)', 'Taxi, Car/Van Service', 'Auto Driver/Passenger', 'Walk (bike)', 'At-Home/Refused'], index = [1,2,3,4,5,6,7,8,9,10])

	#df_modes = pd.concat([s_mode_name.rename('mode'), s_mode_count_wkdy.rename('weekday'), s_mode_count_sat.rename('saturday'),\
	#  s_mode_count_sun.rename('sunday')], axis=1)
	df_modes = pd.concat([s_mode_name.rename('mode'), s_mode_count.rename('count')], axis=1)
	df_modes.sort_values('count', inplace=True,  ascending=False)
	print df_modes

	ax = df_modes.plot(x='mode',  kind='barh', rot=0, legend=False, color='rbbrrrbbbb')
	ax.set_xlabel('Frequency')
	ax.set_ylabel('Mode')
	#ax = df_modes['count'].plot(kind='pie', autopct='%.2f')
	fig = ax.get_figure()
	fig.savefig(chart_name, bbox_inches='tight')

def travels_per_purpose(df_trips_wkdy, df_trips_sat, df_trips_sun, chart_path):

	s_origin_purpose_wkdy = df_trips_wkdy.groupby('O_PURP')['TRIP_ID'].count()
	s_origin_purpose_sat = df_trips_sat.groupby('O_PURP')['TRIP_ID'].count()
	s_origin_purpose_sun = df_trips_sun.groupby('O_PURP')['TRIP_ID'].count()

	s_destination_purpose_wkdy = df_trips_wkdy.groupby('D_PURP')['TRIP_ID'].count()
	s_destination_purpose_sat = df_trips_sat.groupby('D_PURP')['TRIP_ID'].count()
	s_destination_purpose_sun = df_trips_sun.groupby('D_PURP')['TRIP_ID'].count()

	s_purpose_name = pd.Series(['REFUSED', 'USUAL WORKPLACE', 'OTHR WORKPLACE / WORK RELATED', 'SCHOOL (PERSONAL)', 'DROP OFF OR PICK UP SOMEONE',\
	 'SHOPPING', 'ERRANDS OR PERSONAL BUSINESS', 'MEDICAL OR OTHER PROFESSIONAL SERVICES', 'EAT OUT',' MOVIES, GYM, SPORTS, OTHER ENTERTAINMENT',\
	'VISIT FRIENDS, FAMILY', 'HOME', 'CHANGE MODE/ TRANSFER', 'OTHER: TYPE IN COMMENTS BOX'], index=[0,12,13,14,15,16,17,18,19,20,21,22,96,97])

	df_origin_purposes = pd.concat([s_purpose_name.rename('purpose'), s_origin_purpose_wkdy.rename('weekday'),\
	 s_origin_purpose_sat.rename('saturday'), s_origin_purpose_sun.rename('sunday')], axis=1)

	df_destination_purposes = pd.concat([s_purpose_name.rename('purpose'), s_destination_purpose_wkdy.rename('weekday'),\
	 s_destination_purpose_sat.rename('saturday'), s_destination_purpose_sun.rename('sunday')], axis=1)

	print df_origin_purposes
	print ''
	print df_destination_purposes

	ax = df_origin_purposes.plot(x='purpose', y=['weekday', 'saturday', 'sunday'], color=['g', 'y', 'r'], kind='bar', rot=90)
	ax.set_title('Origin Purposes')
	fig = ax.get_figure()
	fig.savefig(chart_path + 'origin_purposes.png', bbox_inches='tight')

	ax = df_destination_purposes.plot(x='purpose', y=['weekday', 'saturday', 'sunday'], color=['g', 'y', 'r'], kind='bar', rot=90)
	ax.set_title('Destination  Purposes')
	fig = ax.get_figure()
	fig.savefig(chart_path + 'destination_purposes.png', bbox_inches='tight')

def aggregate_counties_out_of_area(series_area_count, list_names):
	list_area_count = []
	count_out_of_area = 0
	for county, count in series_area_count.iteritems():
		county = county.strip()
		if county.strip() in list_names:
			list_area_count.append((county, count))
		else:
			count_out_of_area += count

	list_area_count.append(('Out of Area', count_out_of_area))

	return list_area_count

def travels_per_county(df_trips_wkdy, df_trips_sat, df_trips_sun, chart_path):
	nyc_counties = ['Bronx', 'Kings', 'New York', 'Queens', 'Richmond']

	s_county_origin_wkdy = df_trips_wkdy.groupby('O_COUNTY_STR')['TRIP_ID'].count()
	s_county_origin_sat = df_trips_sat.groupby('O_COUNTY_STR')['TRIP_ID'].count()
	s_county_origin_sun = df_trips_sun.groupby('O_COUNTY_STR')['TRIP_ID'].count()

	s_county_destination_wkdy = df_trips_wkdy.groupby('D_COUNTY_STR')['TRIP_ID'].count()
	s_county_destination_sat = df_trips_sat.groupby('D_COUNTY_STR')['TRIP_ID'].count()
	s_county_destination_sun = df_trips_sun.groupby('D_COUNTY_STR')['TRIP_ID'].count()

	list_county_origin_wkdy = aggregate_counties_out_of_area(s_county_origin_wkdy, nyc_counties)
	list_county_origin_sat = aggregate_counties_out_of_area(s_county_origin_sat, nyc_counties)
	list_county_origin_sun = aggregate_counties_out_of_area(s_county_origin_sun, nyc_counties)

	list_county_origin_wkdy = list(zip(*list_county_origin_wkdy))
	list_county_origin_sat = list(zip(*list_county_origin_sat))
	list_county_origin_sun = list(zip(*list_county_origin_sun))

	list_county_destination_wkdy = aggregate_counties_out_of_area(s_county_destination_wkdy, nyc_counties)
	list_county_destination_sat = aggregate_counties_out_of_area(s_county_destination_sat, nyc_counties)
	list_county_destination_sun = aggregate_counties_out_of_area(s_county_destination_sun, nyc_counties)

	list_county_destination_wkdy = list(zip(*list_county_destination_wkdy))
	list_county_destination_sat = list(zip(*list_county_destination_sat))
	list_county_destination_sun = list(zip(*list_county_destination_sun))

	'''
		Origin
	'''
	fig, ax = plt.subplots()

	x_index = np.arange(len(list_county_origin_wkdy[0]))
	bar_width = 0.3

	ax.bar(x_index, list_county_origin_wkdy[1], bar_width, color='g', label='weekday')
	ax.bar(x_index + bar_width, list_county_origin_sat[1], bar_width, color='y', label='saturday')
	ax.bar(x_index + bar_width*2, list_county_origin_sun[1], bar_width, color='r', label='sunday')

	plt.title('County of Origin')
	plt.xlabel('County')
	plt.xticks(x_index + 3*bar_width/2, list_county_origin_wkdy[0])
	plt.legend()
	plt.tight_layout()

	fig.savefig(chart_path + 'origin_county.png')

	'''
		Destination
	'''
	fig, ax = plt.subplots()

	x_index = np.arange(len(list_county_destination_wkdy[0]))
	bar_width = 0.3

	ax.bar(x_index, list_county_destination_wkdy[1], bar_width, color='g', label='weekday')
	ax.bar(x_index + bar_width, list_county_destination_sat[1], bar_width, color='y', label='saturday')
	ax.bar(x_index + bar_width*2, list_county_destination_sun[1], bar_width, color='r', label='sunday')

	plt.title('County of Destination')
	plt.xlabel('County')
	plt.xticks(x_index + 3*bar_width/2, list_county_destination_wkdy[0])
	plt.legend()
	plt.tight_layout()

	fig.savefig(chart_path + 'destination_county.png')

# # county
def origin_destination_county(df_trips, chart_name):
	nyc_counties = ['Bronx', 'Kings', 'New York', 'Queens', 'Richmond']
	o_counties_in_nyc = []
	o_counties_out_nyc = []
	o_count_in_nyc = 0
	o_count_out_nyc = 0

	d_counties_in_nyc = []
	d_counties_out_nyc = []
	d_count_in_nyc = 0
	d_count_out_nyc = 0

	s_county_origin = df_trips.groupby('O_COUNTY_STR')['TRIP_ID'].count()
	s_county_destination = df_trips.groupby('D_COUNTY_STR')['TRIP_ID'].count()

	for county, count in s_county_origin.iteritems():
		county = county.rstrip()
		if county.rstrip() in nyc_counties:
			o_counties_in_nyc.append((county, count))
			o_count_in_nyc += count
		else:
			o_counties_out_nyc.append((county, count))
			o_count_out_nyc += count

	o_counties_in_nyc.append(('Out of Area', o_count_out_nyc))

	o_counties_in_nyc = list(zip(*o_counties_in_nyc))
	print o_counties_in_nyc

	for county, count in s_county_destination.iteritems():
		county = county.rstrip()
		if county in nyc_counties:
			d_counties_in_nyc.append((county, count))
			d_count_in_nyc += count
		else:
			d_counties_out_nyc.append((county, count))
			d_count_out_nyc += count

	d_counties_in_nyc.append(('Out of Area', d_count_out_nyc))
	d_counties_in_nyc = list(zip(*d_counties_in_nyc))

	print d_counties_in_nyc

	# count counties in and out of nyc boundaries
	fig, ax = plt.subplots()

	x_index = np.arange(len(o_counties_in_nyc[0]))
	bar_width = 0.35

	rects1 = ax.bar(x_index, o_counties_in_nyc[1], bar_width, color='b', label='origin')
	rects2 = ax.bar(x_index + bar_width, d_counties_in_nyc[1], bar_width, color='r', label='destination')

	plt.xlabel('County')

	plt.xticks(x_index + 2*bar_width/2, o_counties_in_nyc[0])
	plt.legend()

	plt.tight_layout()

	fig.savefig('test_od.png')

def origin_destination_purpose(df_trips, chart_name):

	s_purpose_origin = df_trips.groupby('O_PURP')['TRIP_ID'].count()
	s_purpose_destination = df_trips.groupby('D_PURP')['TRIP_ID'].count()

	s_purpose_name = pd.Series(['REFUSED', 'USUAL WORKPLACE', 'OTHR WORKPLACE / WORK RELATED', 'SCHOOL (PERSONAL)', 'DROP OFF OR PICK UP SOMEONE',\
	 'SHOPPING', 'ERRANDS OR PERSONAL BUSINESS', 'MEDICAL OR OTHER PROFESSIONAL SERVICES', 'EAT OUT',' MOVIES, GYM, SPORTS, OTHER ENTERTAINMENT',\
	'VISIT FRIENDS, FAMILY', 'HOME', 'CHANGE MODE/ TRANSFER', 'OTHER: TYPE IN COMMENTS BOX'], index=[0,12,13,14,15,16,17,18,19,20,21,22,96,97])

	df_od_purposes = pd.concat([s_purpose_name.rename('purpose'), s_purpose_origin.rename('origin'), s_purpose_destination.rename('destination')],\
	 axis=1)
	print df_od_purposes

	ax = df_od_purposes.plot(x='purpose', y=['origin', 'destination'], color=['b', 'r'], kind='bar', rot=90)
	fig = ax.get_figure()
	fig.savefig(chart_name, bbox_inches='tight')

def origin_destination_nyc_transit(df_trips, chart_name):
	df_transit_trips = df_trips[df_trips['MODE_G2'] == 1]
	origin_destination_county(df_transit_trips, chart_name)

def get_travel_time(s_trip):
	try:
		departure_time = datetime.strptime(s_trip['trip_sdate'].split(' ')[0] + ' ' + s_trip['dtime'], '%m/%d/%y %H:%M')
		arrival_time = datetime.strptime(s_trip['trip_edate'].split(' ')[0] + ' ' + s_trip['atime'], '%m/%d/%y %H:%M')
		travel_time = (arrival_time - departure_time).seconds/60 # travel time in minutes
	except ValueError:
		travel_time = -1
	return travel_time

def cut_borders(list_values, min_value, max_value):
	new_list = []
	for value in list_values:
		if value > max_value:
			new_list.append(max_value)
		elif value < min_value:
			new_list.append(min_value)
		else:
			new_list.append(value)

	return new_list

# cdf of overall travel time
def total_travel_duration(df_trips_wkdy, df_trips_sat, df_trips_sun, chart_name):
	list_travel_time_wkdy = []
	list_travel_time_sat = []
	list_travel_time_sun = []

	for index, s_trip in df_trips_wkdy.iterrows():
		travel_time = get_travel_time(s_trip)
		if travel_time != -1:
			list_travel_time_wkdy.append(travel_time)

	for index, s_trip in df_trips_sat.iterrows():
		travel_time = get_travel_time(s_trip)
		if travel_time != -1:
			list_travel_time_sat.append(travel_time)

	for index, s_trip in df_trips_sun.iterrows():
		travel_time = get_travel_time(s_trip)
		if travel_time != -1:
			list_travel_time_sun.append(travel_time)

	# set threshold as 5 hours (300 minutes)
	list_travel_time_wkdy = cut_borders(list_travel_time_wkdy, 0,300)
	list_travel_time_sat = cut_borders(list_travel_time_sat, 0, 300)
	list_travel_time_sun = cut_borders(list_travel_time_sun, 0, 300)


	list_travel_time_wkdy.sort()
	ecdf_travel_time_wkdy = ECDF(list_travel_time_wkdy)

	list_travel_time_sat.sort()
	ecdf_travel_time_sat = ECDF(list_travel_time_sat)

	list_travel_time_sun.sort()
	ecdf_travel_time_sun = ECDF(list_travel_time_sun)

	fig, ax = plt.subplots()
	plt.plot(ecdf_travel_time_wkdy.x, ecdf_travel_time_wkdy.y, label='weekday')
	plt.plot(ecdf_travel_time_sat.x, ecdf_travel_time_sat.y, label='saturday')
	plt.plot(ecdf_travel_time_sun.x, ecdf_travel_time_sun.y, label='sunday')

	ax.xaxis.set_major_locator(ticker.MultipleLocator(60)) # set x sticks interal
	plt.grid()
	plt.legend()
	ax.set_title('ECDF travel Time')
	plt.tight_layout()
	fig.savefig(chart_name)

def travel_duration_per_mode(df_trips, chart_name):
	# s_mode_name_10 = pd.Series(['NYC Subway Only', 'NYC Subway + Bus', 'NY or MTA Bus (no sub)', 'Commuter Rail (no nyct)', 'Other Rail (no nyct)',\
	# 'Other Transit (no nyct)', 'Taxi, Car/Van Service', 'Auto Driver/Passenger', 'Walk (bike)', 'At-Home/Refused'], index = [1,2,3,4,5,6,7,8,9,10])

	s_mode_name_8 = pd.Series(['NYC Subway', 'Subway + Bus', 'NY-MTA Bus (only)', 'Other Transit', 'Taxi, Car/Van', 'Auto', 'Walk (bike)',\
	 'At-Home/Refused'], index = [1,2,3,4,5,6,7,8])

	dict_commute_time_mode = dict()

	for index, s_trip in df_trips.iterrows():
		dict_commute_time_mode.setdefault(s_trip['MODE_G8'], list()).append(get_travel_time(s_trip))
		#break

	# remove 'At Home/Refused'
	del dict_commute_time_mode[4]
	del dict_commute_time_mode[6]
	del dict_commute_time_mode[7]
	del dict_commute_time_mode[8]

	fig, ax = plt.subplots()
	for key, list_time in dict_commute_time_mode.iteritems():
		list_time = cut_borders(list_time, 0, 360)
		list_time.sort()
		ecdf = ECDF(list_time)
		plt.plot(ecdf.x, ecdf.y, label=s_mode_name_8[key])
		print key, ':', len(list_time)
	print ''

	ax.xaxis.set_major_locator(ticker.MultipleLocator(60)) # set x ticks as multiple of sixty
	plt.grid()
	plt.legend(loc=4)
	# ax.set_title('')
	ax.set_xlabel('Informed Trip Duration (minutes)')
	ax.set_ylabel('ECDF')
	plt.tight_layout()
	fig.savefig(chart_name)

def format_puma_code(puma_survey):
	return str(puma_survey).split('.')[0][3:]

# count the amount of interviewrs departuring from home per PUMA
def get_count_origins_per_puma(df_trips, origin_type):
	s_origin_type = pd.Series(['Home', 'Work', 'School', 'Some other place'], index=[1,2,3,4])
	dict_puma_origin_type = dict()
	for index, s_trip in df_trips.iterrows():
		dict_puma_origin_type.setdefault(s_trip['otype'], list()).append(format_puma_code(s_trip['O_PUMA']))

	if origin_type in s_origin_type.index.values.tolist():
		# count homes per puma
		dict_puma_count = dict()
		for puma in dict_puma_origin_type[origin_type]:
			if puma in dict_puma_count.keys():
				dict_puma_count[puma] = dict_puma_count[puma] + 1
			else:
				dict_puma_count[puma] = 1
	else:
		dict_puma_count = dict()
		# count homes per puma
		for index in s_origin_type.index.values.tolist():
			for puma in dict_puma_origin_type[index]:
				if puma in dict_puma_count.keys():
					dict_puma_count[puma] = dict_puma_count[puma] + 1
				else:
					dict_puma_count[puma] = 1

	for puma, count in dict_puma_count.iteritems():
		print puma, count

	return dict_puma_count

def get_count_destinations_per_puma(df_trips, destination_type):
	s_destination_type = pd.Series(['Home', 'Work', 'School', 'Some other place'], index=[1,2,3,4])
	dict_puma_destination_type = dict()
	for index, s_trip in df_trips.iterrows():
		dict_puma_destination_type.setdefault(s_trip['dtype'], list()).append(format_puma_code(s_trip['D_PUMA']))

	if destination_type in s_destination_type.index.values.tolist():
		#dict_puma_destination_type = dict_puma_destination_type[destination_type]

		# count homes per puma
		dict_puma_count = dict()
		for puma in dict_puma_destination_type[destination_type]:
			if puma in dict_puma_count.keys():
				dict_puma_count[puma] = dict_puma_count[puma] + 1
			else:
				dict_puma_count[puma] = 1

	else:
		dict_puma_count = dict()
		# count homes per puma
		for index in s_destination_type.index.values.tolist():
			for puma in dict_puma_destination_type[index]:
				if puma in dict_puma_count.keys():
					dict_puma_count[puma] = dict_puma_count[puma] + 1
				else:
					dict_puma_count[puma] = 1

	for puma, count in dict_puma_count.iteritems():
		print puma, count

	return dict_puma_count

def get_subway_stations_per_puma(shp_subway_stations, shp_puma):
	subway_stations = gpd.GeoDataFrame.from_file(shp_subway_stations)
	print 'len stations', len(subway_stations)
	nyc_puma = gpd.GeoDataFrame.from_file(shp_puma)
	print 'len puma', len(nyc_puma)

	stations_in_pumas = sjoin(subway_stations, nyc_puma, how='left')
	grouped = stations_in_pumas.groupby('index_right')

	dict_puma_count = dict()
	for key, list_points in grouped.groups.iteritems():
		puma = stations_in_pumas[stations_in_pumas['index_right'] == key]['puma'].iloc[0]
		dict_puma_count[puma] = len(list_points)

	print dict_puma_count

	return dict_puma_count

def plot_puma(shapefile_base_path, dict_puma_count, map_title, map_path):

	shapefile_puma = shapefile.Reader(shapefile_base_path)

	# set range of colors
	# cmap = plt.cm.GnBu
	#cmap = plt.cm.Blues
	#cmap = plt.cm.OrRd
	#cmap = plt.cm.Purples
	# cmap = plt.cm.Reds
	cmap = plt.cm.Greens
	vmin = min(dict_puma_count.values()); vmax = max(dict_puma_count.values())
	norm = Normalize(vmin=vmin, vmax=vmax)

	# color mapper to covert values to colors
	mapper = ScalarMappable(norm=norm, cmap=cmap)

	list_nyc_pumas = []
	for row in shapefile_puma.iterShapeRecords():
		list_nyc_pumas.append(row.record[0])

	# set colors to each puma
	colors = dict()
	# for key, count in dict_puma_count.iteritems():
	# 	if key in list_nyc_pumas:
	# 	colors[key] = mapper.to_rgba(count)

	for puma in list_nyc_pumas:
		if puma in dict_puma_count.keys():
			colors[puma] = mapper.to_rgba(dict_puma_count[puma])
		else:
			colors[puma] = (1.0,1.0,1.0)
			#print rgb2hex('w')

	fig = plt.figure()
	ax = fig.gca()

	# manipulate shapefile
	fields = shapefile_puma.fields[1:]
	field_names = [field[0] for field in fields]

	for record, shape in zip(shapefile_puma.iterRecords(), shapefile_puma.iterShapes()):
		attributes = dict(zip(field_names, record))
		print attributes, shape

		# check number of parts (could use MultiPolygon class of shapely?)
		nparts = len(shape.parts) # total parts
		if nparts == 1:
			polygon = Polygon(shape.points)
			facecolor = rgb2hex(colors[attributes['puma']])
			patch = PolygonPatch(polygon, alpha=1.0, zorder=2, facecolor=facecolor, linewidth=.25)
			ax.add_patch(patch)

		else: # loop over parts of each shape, plot separately
			for ip in range(nparts): # loop over parts, plot separately
				i0=shape.parts[ip]
				if ip < nparts-1:
					i1 = shape.parts[ip+1]-1
				else:
					i1 = len(shape.points)

				polygon = Polygon(shape.points[i0:i1+1])
				facecolor = rgb2hex(colors[attributes['puma']])
				patch = PolygonPatch(polygon, alpha=1.0, zorder=2, facecolor=facecolor, linewidth=.25)
				ax.add_patch(patch)

	    #icolor = icolor + 1
	ax.axis('scaled')
	plt.xticks([])
	plt.yticks([])
	ax.set_title(map_title)

	ax.set_yscale('log')

	# range color legend
	cax = fig.add_axes([0.85, 0.25, 0.05, 0.5]) # posititon
	cb = ColorbarBase(cax,cmap=cmap,norm=norm, orientation='vertical')

	#fig.tight_layout()
	fig.savefig(map_path)


def plot_census_tranct(shapefile_base_path, dict_ct_count, map_title, map_path):

	shapefile_puma = shapefile.Reader(shapefile_base_path)

	# set range of colors
	cmap = plt.cm.GnBu
	#cmap = plt.cm.Blues
	#cmap = plt.cm.OrRd
	#cmap = plt.cm.Purples
	# cmap = plt.cm.Reds
	#cmap = plt.cm.Greens
	vmin = min(dict_census_tract_count.values()); vmax = max(dict_census_tract_count.values())
	norm = Normalize(vmin=vmin, vmax=vmax)

	# color mapper to covert values to colors
	mapper = ScalarMappable(norm=norm, cmap=cmap)

	list_nyc_census_tracts = []
	for row in shapefile_census_tract.iterShapeRecords():
		list_nyc_census_tracts.append(row.record[0])

	# set colors to each census_tract
	colors = dict()
	# for key, count in dict_census_tract_count.iteritems():
	# 	if key in list_nyc_census_tracts:
	# 	colors[key] = mapper.to_rgba(count)

	for census_tract in list_nyc_census_tracts:
		if census_tract in dict_census_tract_count.keys():
			colors[census_tract] = mapper.to_rgba(dict_census_tract_count[census_tract])
		else:
			colors[census_tract] = (1.0,1.0,1.0)
			#print rgb2hex('w')

	fig = plt.figure()
	ax = fig.gca()

	# manipulate shapefile
	fields = shapefile_census_tract.fields[1:]
	field_names = [field[0] for field in fields]

	for record, shape in zip(shapefile_census_tract.iterRecords(), shapefile_census_tract.iterShapes()):
		attributes = dict(zip(field_names, record))
		print attributes, shape

		# check number of parts (could use MultiPolygon class of shapely?)
		nparts = len(shape.parts) # total parts
		if nparts == 1:
			polygon = Polygon(shape.points)
			facecolor = rgb2hex(colors[attributes['ct_2010']])
			patch = PolygonPatch(polygon, alpha=1.0, zorder=2, facecolor=facecolor, linewidth=.25)
			ax.add_patch(patch)

		else: # loop over parts of each shape, plot separately
			for ip in range(nparts): # loop over parts, plot separately
				i0=shape.parts[ip]
				if ip < nparts-1:
					i1 = shape.parts[ip+1]-1
				else:
					i1 = len(shape.points)

				polygon = Polygon(shape.points[i0:i1+1])
				facecolor = rgb2hex(colors[attributes['ct_2010']])
				patch = PolygonPatch(polygon, alpha=1.0, zorder=2, facecolor=facecolor, linewidth=.25)
				ax.add_patch(patch)

	    #icolor = icolor + 1
	ax.axis('scaled')
	plt.xticks([])
	plt.yticks([])
	ax.set_title(map_title)

	# ax.set_yscale('log')

	# range color legend
	cax = fig.add_axes([0.85, 0.25, 0.05, 0.5]) # posititon
	cb = ColorbarBase(cax,cmap=cmap,norm=norm, orientation='vertical')

	#fig.tight_layout()
	fig.savefig(map_path)



def matrix_od_county(df_trips):
	dict_county_od = dict()

	nyc_counties = ['Bronx', 'Kings', 'New York', 'Queens', 'Richmond']

	for index, trip in df_trips.iterrows():
		o_county = trip['O_COUNTY_STR'].rstrip()
		d_county = trip['D_COUNTY_STR'].rstrip()

		if o_county in nyc_counties and d_county in nyc_counties:
			if o_county not in dict_county_od.keys():
				dict_county_od[o_county] = dict()
			elif d_county not in dict_county_od[o_county].keys():
				dict_county_od[o_county][d_county] = 1
			else:
				dict_county_od[o_county][d_county] += 1

	for key, od_county in dict_county_od.iteritems():
		print key, od_county

 	print ''

	return dict_county_od

def od_matrix(df_trips_wkdy, df_trips_sat, df_trips_sun):
	# all modes
	matrix_od_county(df_trips_wkdy)
	matrix_od_county(df_trips_sat)
	matrix_od_county(df_trips_sun)

	# transit
	print 'transit'
	matrix_od_county(df_trips_wkdy[df_trips_wkdy['MODE_G2'] == 1])
	matrix_od_county(df_trips_sat[df_trips_sat['MODE_G2'] == 1])
	matrix_od_county(df_trips_sun[df_trips_sun['MODE_G2'] == 1])

	# non transit
	print 'non transit'
	matrix_od_county(df_trips_wkdy[df_trips_wkdy['MODE_G2'] == 2])
	matrix_od_county(df_trips_sat[df_trips_sat['MODE_G2'] == 2])
	matrix_od_county(df_trips_sun[df_trips_sun['MODE_G2'] == 2])

	#print dict_county_od

df_trips_wkdy = df_from_csv(travel_survey_file_wkdy)
df_trips_sat = df_from_csv(travel_survey_file_sat)
df_trips_sun = df_from_csv(travel_survey_file_sun)
df_trips = pd.concat([df_trips_wkdy, df_trips_sat, df_trips_sun])

# total_departure_arrival_trips(df_trips, chart_path + 'departure_time_modes.png')
#origin_destination_county(df_trips, chart_path + 'origin_destination_county.png')
#origin_destination_nyc_transit(df_trips, chart_path + 'od_transit.png')
#origin_destination_purpose(df_trips, chart_path + 'od_purpose.png')

travels_per_mode(df_trips_wkdy, df_trips_sat, df_trips_sun, chart_path + 'travels_per_mode.png')
# travels_per_purpose(df_trips_wkdy, df_trips_sat, df_trips_sun, chart_path)
#travels_per_county(df_trips_wkdy, df_trips_sat, df_trips_sun, chart_path)

# total_travel_duration(df_trips_wkdy, df_trips_sat, df_trips_sun, 'travel_time.png')

# travel_duration_per_mode(df_trips_wkdy, chart_path + 'travel_time_mode_wkdy.png')
# travel_duration_per_mode(df_trips_sat, chart_path + 'travel_time_mode_sat.png')
# travel_duration_per_mode(df_trips_sun, chart_path + 'travel_time_mode_sun.png')

# travel_duration_per_mode(df_trips, chart_path + 'travel_time_mode.png')

# plot_puma(shp_puma, get_count_origins_per_puma(df_trips_wkdy, 1), 'Number of Origins at Home per PUMA on Weekdays', chart_path + 'home_origin_puma_wkdy.png')
# plot_puma(shp_puma, get_count_origins_per_puma(df_trips_sat, 1), 'Number of Origins at Home per PUMA on Satuday', chart_path + 'home_origin_puma_sat.png')
# plot_puma(shp_puma, get_count_origins_per_puma(df_trips_sun, 1), 'Number of Origins at Home per PUMA on Sunday', chart_path + 'home_origin_puma_sun.png')

# plot_puma(shp_puma, get_count_origins_per_puma(df_trips_wkdy, 2), 'Number of Origins at Work per PUMA on Weekdays', chart_path + 'work_origin_puma_wkdy.png')
# plot_puma(shp_puma, get_count_origins_per_puma(df_trips_sat, 2), 'Number of Origins at Work per PUMA on Saturday', chart_path + 'work_origin_puma_sat.png')
# plot_puma(shp_puma, get_count_origins_per_puma(df_trips_sun, 2), 'Number of Origins at Work per PUMA on Sunday', chart_path + 'work_origin_puma_sun.png')

# plot_puma(shp_puma, get_count_origins_per_puma(df_trips_wkdy, 3), 'Number of Origins at School per PUMA on Weekdays', chart_path + 'school_origin_puma_wkdy.png')
# plot_puma(shp_puma, get_count_origins_per_puma(df_trips_sat, 3), 'Number of Origins at School per PUMA on Saturday', chart_path + 'school_origin_puma_sat.png')
# plot_puma(shp_puma, get_count_origins_per_puma(df_trips_sun, 3), 'Number of Origins at School per PUMA on Sunday', chart_path + 'school_origin_puma_sun.png')

# plot_puma(shp_puma, get_count_origins_per_puma(df_trips_sun, 3), 'Number of Origins at School per PUMA on Sunday', chart_path + 'school_origin_puma_sun.png')

# plot_puma(shp_puma, get_count_destinations_per_puma(df_trips_wkdy, 2), 'Number of Destinations at Work per PUMA on Weekdays', chart_path + 'work_destination_puma_wkdy.png')
# plot_puma(shp_puma, get_count_destinations_per_puma(df_trips_sat, 2), 'Number of Destinations at Work per PUMA on Saturday', chart_path + 'work_destination_puma_sat.png')
# plot_puma(shp_puma, get_count_destinations_per_puma(df_trips_sun, 2), 'Number of Destinations at Work per PUMA on Sunday', chart_path + 'work_destination_puma_sun.png')

# plot_puma(shp_puma, get_count_destinations_per_puma(df_trips_wkdy, 3), 'Number of Destinations at School per PUMA on Weekdays', chart_path + 'school_destination_puma_wkdy.png')
# plot_puma(shp_puma, get_count_destinations_per_puma(df_trips_sat, 3), 'Number of destinations at School per PUMA on Saturday', chart_path + 'school_destination_puma_sat.png')
# plot_puma(shp_puma, get_count_destinations_per_puma(df_trips_sun, 3), 'Number of Destinations at School per PUMA on Sunday', chart_path + 'school_destination_puma_sun.png')

# plot_puma(shp_puma, get_count_origins_per_puma(df_trips_sun, 5), 'Number of Origins per PUMA on Sunday', chart_path + 'origins_puma_sun.png')
# plot_puma(shp_puma, get_count_origins_per_puma(df_trips_sat, 5), 'Number of Origins per PUMA on Saturday', chart_path + 'origins_puma_sat.png')
# plot_puma(shp_puma, get_count_origins_per_puma(df_trips_wkdy, 5), 'Number of Origins per PUMA on Weekday', chart_path + 'origins_puma_wkdy.png')
# plot_puma(shp_puma, get_count_origins_per_puma(df_trips, 5), 'Number of Origins per PUMA', chart_path + 'origins_puma.png')

# plot_puma(shp_puma, get_count_destinations_per_puma(df_trips_sun, 5), 'Number of Destinations per PUMA on Sunday', chart_path + 'destination_puma_sun.png')
# plot_puma(shp_puma, get_count_destinations_per_puma(df_trips_sat, 5), 'Number of Destinations per PUMA on Saturday', chart_path + 'destination_puma_sat.png')
# plot_puma(shp_puma, get_count_destinations_per_puma(df_trips_wkdy, 5), 'Number of Destinations per PUMA on Weekday', chart_path + 'destination_puma_wkdy.png')
# plot_puma(shp_puma, get_count_destinations_per_puma(df_trips, 5), 'Number of Destinations per PUMA', chart_path + 'destination_puma.png')

# df_trips_transit = df_trips[df_trips['MODE_G2'] == 1]
# plot_puma(shp_puma, get_count_origins_per_puma(df_trips_transit, 5), 'Transit Origins per PUMA', chart_path + 'origins_transit_puma.png')
# # plot_puma(shp_puma, get_count_destinations_per_puma(df_trips_transit, 5), ' Transit Destinations per PUMA', chart_path + 'destination_transit_puma.png')
# df_trips_taxi = df_trips[df_trips['MODE_G10'] == 7]
# plot_puma(shp_puma, get_count_origins_per_puma(df_trips_taxi, 5), 'Taxi Origins per PUMA', chart_path + 'origins_taxi_puma.png')
# plot_puma(shp_puma, get_count_destinations_per_puma(df_trips_taxi, 5), 'Taxi Destinations per PUMA', chart_path + 'destination_taxi_puma.png')

#od_matrix(df_trips_wkdy, df_trips_sat, df_trips_sun)

#get_subway_stations_per_puma(shp_subway_stations, shp_puma)
# plot_puma(shp_puma, get_subway_stations_per_puma(shp_subway_stations, shp_puma), 'Number of stations per PUMA', chart_path + 'subway_puma.png')
#
# def print_sample(df_trips):
# 	for index in range(10):
# 		print 'sampn', df_trips.iloc[index]['sampn']
# 		print 'perno', df_trips.iloc[index]['perno']
# 		print 'tripno', df_trips.iloc[index]['tripno']
# 		print 'TRIP_ID', df_trips.iloc[index]['TRIP_ID']
# 		print ''
# 		print 'daywk', df_trips.iloc[index]['daywk']
# 		print 'HR_DEP', df_trips.iloc[index]['HR_DEP']
# 		print 'dtime', df_trips.iloc[index]['dtime']
# 		print 'trip_sdate', df_trips.iloc[index]['trip_sdate']
# 		print 'HR_ARR', df_trips.iloc[index]['HR_ARR']
# 		print 'atime', df_trips.iloc[index]['atime']
# 		print 'trip_edate', df_trips.iloc[index]['trip_edate']
# 		print ''
# 		print 'ussob', df_trips.iloc[index]['ussob']
# 		print 'MODE_G2', df_trips.iloc[index]['MODE_G2']
# 		print 'MODE_G10', df_trips.iloc[index]['MODE_G10']
# 		print 'trip_count', df_trips.iloc[index]['trip_count']
# 		print 'MODE1', df_trips.iloc[index]['MODE1']
# 		print 'MODE2', df_trips.iloc[index]['MODE2']
# 		print 'MODE3', df_trips.iloc[index]['MODE3']
# 		print 'MODE4', df_trips.iloc[index]['MODE4']
# 		print 'MODE5', df_trips.iloc[index]['MODE5']
# 		print 'MODE6', df_trips.iloc[index]['MODE6']
# 		print 'MODE7', df_trips.iloc[index]['MODE7']
# 		print 'MODE8', df_trips.iloc[index]['MODE8']
# 		print 'MODE9', df_trips.iloc[index]['MODE9']
# 		print 'MODE10', df_trips.iloc[index]['MODE10']
# 		print 'MODE11', df_trips.iloc[index]['MODE11']
# 		print 'MODE12', df_trips.iloc[index]['MODE12']
# 		print 'MODE13', df_trips.iloc[index]['MODE13']
# 		print 'MODE14', df_trips.iloc[index]['MODE14']
# 		print 'MODE15', df_trips.iloc[index]['MODE15']
# 		print 'MODE16', df_trips.iloc[index]['MODE16']
# 		print ''
# 		print 'R_BORO', df_trips.iloc[index]['R_BORO']
# 		print ''
# 		print 'otype', df_trips.iloc[index]['otype']
# 		print 'O_PURP', df_trips.iloc[index]['O_PURP']
# 		print 'O_Boro', df_trips.iloc[index]['O_Boro']
# 		print 'O_COUNTY_STR', df_trips.iloc[index]['O_COUNTY_STR']
# 		print 'O_COUNTY', df_trips.iloc[index]['O_COUNTY']
# 		print 'O_PUMA', df_trips.iloc[index]['O_PUMA']
# 		print 'O_TRACT', df_trips.iloc[index]['O_TRACT']
# 		print ''
# 		print 'dtype', df_trips.iloc[index]['dtype']
# 		print 'D_PURP', df_trips.iloc[index]['D_PURP']
# 		print 'D_Boro', df_trips.iloc[index]['D_Boro']
# 		print 'D_COUNTY_STR', df_trips.iloc[index]['D_COUNTY_STR']
# 		print 'D_COUNTY', df_trips.iloc[index]['D_COUNTY']
# 		print 'D_PUMA', df_trips.iloc[index]['D_PUMA']
# 		print 'D_TRACT', df_trips.iloc[index]['D_TRACT']
# 		print ''
# 		print 'NSUB', df_trips.iloc[index]['NSUB']
# 		print 'NNYBUS', df_trips.iloc[index]['NNYBUS']
# 		print 'NCRAIL', df_trips.iloc[index]['NCRAIL']
# 		print 'NOTHTRAN', df_trips.iloc[index]['NOTHTRAN']
# 		print 'StopAreaNo', df_trips.iloc[index]['StopAreaNo']
# 		print '================================================='

#print_sample(df_trips)
