'''
    Print distance distributions of each trip segment
'''
from sys import argv
import pandas as pd

import matplotlib.pyplot as plt
from statsmodels.distributions.empirical_distribution import ECDF

private_trips = argv[1]
matches_path = argv[2]
result_path = argv[3]

# read and transform
df_private = pd.read_csv(private_trips)
df_matches = pd.read_csv(matches_path)
print df_matches
df_private = df_private[df_private['sampn_perno_tripno']\
.isin(set(df_matches['transit_id'].unique() | df_matches['taxi_id'].unique()))]
df_matches['transit_destination_time'] = pd.to_datetime(df_matches['transit_destination_time'])
df_matches['taxi_destination_time'] = pd.to_datetime(df_matches['taxi_destination_time'])

# get distances
list_integration_distance = []
list_shared_distance = []
list_destinations_distance = []
for index, match in df_matches.iterrows():
    total_distance = match['integration_distance'] + match['shared_distance'] + match['destinations_distance']
    list_integration_distance.append(match['integration_distance']/total_distance)
    list_shared_distance.append(match['shared_distance']/total_distance)
    list_destinations_distance.append(match['destinations_distance']/total_distance)

# plot
list_integration_distance.sort()
list_shared_distance.sort()
list_destinations_distance.sort()

ecdf_integration_distance = ECDF(list_integration_distance)
ecdf_shared_distance = ECDF(list_shared_distance)
ecdf_destinations_distance = ECDF(list_destinations_distance)

fig, ax = plt.subplots()
plt.plot(ecdf_integration_distance.x, ecdf_integration_distance.y, label='integration duration')
plt.plot(ecdf_shared_distance.x, ecdf_shared_distance.y, label='shared duration')
plt.plot(ecdf_destinations_distance.x, ecdf_destinations_distance.y, label='destinations duration')

plt.grid()
plt.legend()
ax.set_xlabel('segment duration / total duration')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(result_path)
