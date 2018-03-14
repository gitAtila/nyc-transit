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

travel_survey_file_wkdy = argv[1]
travel_survey_file_sat = argv[2]
travel_survey_file_sun = argv[3]
shp_puma = argv[4]

spatial_result_path = argv[5]

def df_from_csv(travel_survey_file):
	return pd.read_csv(travel_survey_file)

def format_puma_code(puma_survey):
	return str(puma_survey).split('.')[0][3:]

# count the amount of interviewrs departuring from home per PUMA
def get_count_origins_per_puma(df_trips, origin_type):
	s_origin_type = pd.Series(['Casa', 'Trabalho', 'Escola', 'Outro Lugar'], index=[1,2,3,4])
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
	s_destination_type = pd.Series(['Casa', 'Trabalho', 'Escola', 'Outro Lugar'], index=[1,2,3,4])
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

def plot_puma(shapefile_base_path, dict_puma_count, map_title, x_label, range_colors, map_path):

	shapefile_puma = shapefile.Reader(shapefile_base_path)

	# set range of colors
	# cmap = plt.cm.GnBu
	#cmap = plt.cm.Blues
	#cmap = plt.cm.OrRd
	#cmap = plt.cm.Purples
	# cmap = plt.cm.Reds
	#cmap = plt.cm.Greens
	cmap = range_colors
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
	ax.set_xlabel(x_label)

	# ax.set_yscale('log')

	# range color legend
	cax = fig.add_axes([0.85, 0.25, 0.05, 0.5]) # posititon
	cb = ColorbarBase(cax,cmap=cmap,norm=norm, orientation='vertical')

	fig.tight_layout()
	fig.savefig(map_path)


df_trips_wkdy = df_from_csv(travel_survey_file_wkdy)
df_trips_sat = df_from_csv(travel_survey_file_sat)
df_trips_sun = df_from_csv(travel_survey_file_sun)
df_trips = pd.concat([df_trips_wkdy, df_trips_sat, df_trips_sun])

# transit
df_trips_transit = df_trips[df_trips['MODE_G2'] == 1]
plot_puma(shp_puma, get_count_origins_per_puma(df_trips_transit, 5), 'Transporte Coletivo', 'Origens',\
plt.cm.Greens, spatial_result_path + 'origens_coletivo_puma.png')
plot_puma(shp_puma, get_count_destinations_per_puma(df_trips_transit, 5), '', 'Destinos',\
plt.cm.Reds, spatial_result_path + 'destinos_coletivo_puma.png')
# taxi
df_trips_taxi = df_trips[df_trips['MODE_G10'] == 7]
plot_puma(shp_puma, get_count_origins_per_puma(df_trips_taxi, 5), 'Transporte Particular','',\
plt.cm.Greens, spatial_result_path + 'origens_taxi_puma.png')
plot_puma(shp_puma, get_count_destinations_per_puma(df_trips_taxi, 5), '','',\
plt.cm.Reds, spatial_result_path + 'destinos_taxi_puma.png')
