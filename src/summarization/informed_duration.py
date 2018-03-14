# read and processing bus data survey
from sys import argv
import pandas as pd
from datetime import datetime
import csv

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from statsmodels.distributions.empirical_distribution import ECDF

travel_survey_file_wkdy = argv[1]
travel_survey_file_sat = argv[2]
travel_survey_file_sun = argv[3]
temporal_result_path = argv[4]

def df_from_csv(travel_survey_file):
	return pd.read_csv(travel_survey_file)

def df_normaliser(df):
	return df.T.div(df.sum(axis=0), axis=0).T

# total departure and arrival time by hour
def demand_time(df_trips, chart_name):

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
	df_total_grouped_hour = pd.concat([departure_subway.rename('Metro'),\
	departure_subway_bus.rename('Metro + Onibus'), departure_bus.rename('Onibus'),\
	departure_taxi.rename('Taxi, Servicos Carro/Van')], axis=1)

	df_total_grouped_hour = df_total_grouped_hour.drop(99)

	print df_total_grouped_hour
	df_total_grouped_hour = df_normaliser(df_total_grouped_hour)

	print df_total_grouped_hour
	ax = df_total_grouped_hour.plot()
	ax.xaxis.set_major_locator(ticker.MultipleLocator(3)) # set x sticks interal
	ax.set_xlabel('Hora')
	ax.set_ylabel('% das Viagens')
	plt.tight_layout()
	fig = ax.get_figure()
	fig.savefig(chart_name)

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

def travel_duration_per_mode(df_trips, chart_name):
	# s_mode_name_10 = pd.Series(['NYC Subway Only', 'NYC Subway + Bus', 'NY or MTA Bus (no sub)', 'Commuter Rail (no nyct)', 'Other Rail (no nyct)',\
	# 'Other Transit (no nyct)', 'Taxi, Car/Van Service', 'Auto Driver/Passenger', 'Walk (bike)', 'At-Home/Refused'], index = [1,2,3,4,5,6,7,8,9,10])

	s_mode_name_8 = pd.Series(['Metro', 'Metro + Onibus', 'Onibus', 'Outro Transp. Coletivo',\
	'Taxi, Servicos Carro/Van', 'Automovel', 'A pe (bicicleta)',\
	 'Em Casa/Recusado'], index = [1,2,3,4,5,6,7,8])

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
	ax.set_xlabel('Duracao Informada da Viagem (minutos)')
	ax.set_ylabel('CDF')
	plt.tight_layout()
	fig.savefig(chart_name)

df_trips_wkdy = df_from_csv(travel_survey_file_wkdy)
df_trips_sat = df_from_csv(travel_survey_file_sat)
df_trips_sun = df_from_csv(travel_survey_file_sun)
df_trips = pd.concat([df_trips_wkdy, df_trips_sat, df_trips_sun])

demand_time(df_trips, temporal_result_path + 'demanda_por_modal.pdf')
travel_duration_per_mode(df_trips, temporal_result_path + 'duracao_informada_por_modal.pdf')
