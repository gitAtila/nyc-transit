# Find out the correspondence between subway station name in shapefile and in survey
from sys import argv
import shapefile as sf
import pandas as pd
from difflib import SequenceMatcher

shapefile_subway_stations_path = argv[1]
survey_subway_stations_path = argv[2]
equivalence_survey_shapefile = argv[3]
#matching_stations_path = argv[3]

def read_shape_records(shapefile_path):
	shape_file = sf.Reader(shapefile_path)

	fields = shape_file.fields[1:] 
	field_names = [field[0] for field in fields] 

	list_records = []
	for record, shape in zip(shape_file.iterRecords(), shape_file.iterShapes()):
		# All of the shapes in the TM_WORLD_BORDERS dataset have shape.shapeType == 5
		list_records.append(dict(zip(field_names, record)))

	return pd.DataFrame(list_records)

def read_split_survey_stations(survey_subway_stations_path):
	df_survey_subway_stations = pd.read_csv(survey_subway_stations_path)
	# split station name and line
	df_survey_subway_stations['name'], df_survey_subway_stations['line'] = zip(*df_survey_subway_stations['Label'].apply(lambda x: x.split(' (')))
	df_survey_subway_stations['line'] = '(' + df_survey_subway_stations['line'] # Returns with parenthesis on the begining of line

	return df_survey_subway_stations

def get_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

# discover the similarity between names 
# cosidering the most similar inside PUMA
def shapefile_survey_station_similarities(df_shapefile_subway_stations, df_survey_subway_stations, matching_stations_path):
	list_best_match = []
	for index, shape_station in df_shapefile_subway_stations.iterrows():
		sf_station_id = shape_station['objectid']
		sf_station_name = shape_station['name']
		sf_station_line = shape_station['line']
		list_similarities = []

		for key, survey_station in df_survey_subway_stations.iterrows():
			sv_station_id = survey_station['Value']
			sv_station_name = survey_station['name']
			sv_station_line = survey_station['line']
			similarity = get_similarity(sf_station_name + sf_station_line, sv_station_name + sv_station_line)

			list_similarities.append({'sv_station_id': sv_station_id, 'sv_station_name': sv_station_name, 'similarity': similarity})

		list_similarities = sorted(list_similarities, key=lambda k: k['similarity'], reverse=True)
		best_match = list_similarities[0]

		list_best_match.append({'sf_objectid': sf_station_id, 'sf_name': sf_station_name, 'sv_Value': best_match['sv_station_id'],\
		 'sv_name': best_match['sv_station_name'], 'similarity': best_match['similarity']})

	df_best_match = pd.DataFrame(list_best_match)
	df_best_match = df_best_match.sort_values('similarity', ascending=False)
	for index, best_match in df_best_match.iterrows():
		print best_match['sf_name'], '\t',best_match['sv_name'], '\t', best_match['similarity']

	# save correspondence file
	df_best_match.to_csv(matching_stations_path)

# read station names in shapefile
df_shapefile_subway_stations = read_shape_records(shapefile_subway_stations_path)
#print df_shapefile_subway_stations.columns.values

# read station names in survey
df_survey_subway_stations = read_split_survey_stations(survey_subway_stations_path)
#print df_survey_subway_stations.columns.values

#shapefile_survey_station_similarities(df_shapefile_subway_stations, df_survey_subway_stations, matching_stations_path)

df_equivalence_survey_shapefile = pd.read_csv(equivalence_survey_shapefile)
#print df_equivalence_survey_shapefile.columns.values
for index, equivalence in df_equivalence_survey_shapefile.iterrows():
	print equivalence['id'], equivalence['sv_id'], equivalence['sf_id']
	s_survey = df_survey_subway_stations[df_survey_subway_stations['Value'] == equivalence['sv_id']]
	s_shapefile = df_shapefile_subway_stations[df_shapefile_subway_stations['objectid'] == equivalence['sf_id']]

	if s_survey.empty or s_shapefile.empty:
		print 'empty'
	else:
		print s_survey['Label'].iloc[0]
		print s_shapefile['name'].iloc[0], s_shapefile['line'].iloc[0]
	print ''