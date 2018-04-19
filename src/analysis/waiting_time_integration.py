'''
    Compute taxi and transit passengers waiting time at integration stop
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
df_private['date_time'] = pd.to_datetime(df_private['date_time'])
print df_private

df_matches = pd.read_csv(matches_path)
print df_matches
df_matches['transit_destination_time'] = pd.to_datetime(df_matches['transit_destination_time'])
df_matches['taxi_destination_time'] = pd.to_datetime(df_matches['taxi_destination_time'])
df_matches['taxi_arrival_time_transit_stop'] = pd.to_datetime(df_matches['taxi_arrival_time_transit_stop'])

list_taxi_waiting_time = []
list_transit_waiting_time = []
for index, match in df_matches.iterrows():
    # private time
    df_transit_private_trip = df_private[df_private['sampn_perno_tripno']== match['transit_id']]
    transit_integration_datetime = df_transit_private_trip[df_transit_private_trip['stop_id'] == match['stop_id']]['date_time'].iloc[0]

    # waiting time
    if transit_integration_datetime < match['taxi_arrival_time_transit_stop']:
        transit_waiting_time = (match['taxi_arrival_time_transit_stop'] - transit_integration_datetime).total_seconds()
        taxi_waiting_time = 0
    else:
        taxi_waiting_time = (transit_integration_datetime - match['taxi_arrival_time_transit_stop']).total_seconds()
        transit_waiting_time = 0

    list_transit_waiting_time.append(transit_waiting_time/60)
    list_taxi_waiting_time.append(taxi_waiting_time/60)

# plot waiting time
list_transit_waiting_time.sort()
list_taxi_waiting_time.sort()

ecdf_transit_waiting_time = ECDF(list_transit_waiting_time)
ecdf_taxi_waiting_time = ECDF(list_taxi_waiting_time)

fig, ax = plt.subplots()
plt.plot(ecdf_transit_waiting_time.x, ecdf_transit_waiting_time.y, label='transit')
plt.plot(ecdf_taxi_waiting_time.x, ecdf_taxi_waiting_time.y, label='taxi')

plt.grid()
plt.legend()
ax.set_xlabel('waiting time (minutes)')
ax.set_ylabel('CDF')
plt.tight_layout()
fig.savefig(result_path)
