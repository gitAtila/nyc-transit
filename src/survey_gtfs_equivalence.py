'''
    Match survey station code with gtfs station code
'''

from sys import argv
import pandas as pd

gtfs_shape_equivalence_path = argv[1]
survey_shape_equivalence_path = argv[2]
result_path = argv[3]

df_gtfs_shape = pd.read_csv(gtfs_shape_equivalence_path)
df_survey_shape = pd.read_csv(survey_shape_equivalence_path)
list_equivalence = []
for index, survey_shape in df_survey_shape.iterrows():
    survey_id = survey_shape['sf_id']
    gtfs_id = df_gtfs_shape[df_gtfs_shape['objectid'] == survey_shape['sf_id']]['stop_id']
    if len(gtfs_id) >= 1:
        list_equivalence.append({'survey_stop_id': survey_id, 'gtfs_stop_id': gtfs_id.iloc[0]})

df_equivalence_survey_gtfs = pd.DataFrame(list_equivalence)
df_equivalence_survey_gtfs.to_csv(result_path + 'equivalence_survey_gtfs.csv', index=False)
