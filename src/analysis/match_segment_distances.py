'''
    Print distance distributions of each trip segment
'''
from sys import argv
import pandas as pd

import matplotlib.pyplot as plt
from statsmodels.distributions.empirical_distribution import ECDF

matches_path = argv[1]
result_path = argv[2]

# read and transform
df_matches = pd.read_csv(matches_path)
df_matches['transit_destination_time'] = pd.to_datetime(df_matches['transit_destination_time'])
df_matches['taxi_destination_time'] = pd.to_datetime(df_matches['taxi_destination_time'])

# get distances
list_integration_distance = df_matches['integration_distance'].tolist()
list_shared_distance = df_matches['shared_distance'].tolist()
list_taxi_private = []
list_transit_private = []
for index, match in df_matches.iterrows():
    if match['transit_destination_time'] > match['taxi_destination_time']:
        list_transit_private.append(match['destinations_distance'])
    else:
        list_taxi_private.append(match['destinations_distance'])

# plot
list_integration_distance.sort()
list_shared_distance.sort()
list_taxi_private.sort()
list_transit_private.sort()

ecdf_integration_distance = ECDF(list_integration_distance)
ecdf_shared_distance = ECDF(list_shared_distance)
ecdf_taxi_private = ECDF(list_taxi_private)
ecdf_transit_private = ECDF(list_transit_private)

fig, ax = plt.subplots()
plt.plot(ecdf_integration_distance.x, ecdf_integration_distance.y, label='integration distance')
plt.plot(ecdf_shared_distance.x, ecdf_shared_distance.y, label='shared distance')
plt.plot(ecdf_taxi_private.x, ecdf_taxi_private.y, label='taxi private')
plt.plot(ecdf_transit_private.x, ecdf_transit_private.y, label='transit private')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
plt.grid()
plt.legend()
# ax.set_title('saturday')
ax.set_xlabel('match trip segment distances (meters)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(result_path)
