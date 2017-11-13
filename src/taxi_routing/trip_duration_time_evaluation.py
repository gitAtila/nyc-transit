'''
    Compare informed and computed trip duration time
'''
from sys import argv
from datetime import datetime, timedelta
import pandas as pd
import geopandas as gpd

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from statsmodels.distributions.empirical_distribution import ECDF

informed_duration_path = argv[1]
computed_duration_path = argv[2]
chart_name = argv[3]
max_showed_duration = 300 # minutes

df_informed_taxi_duration = pd.read_csv(informed_duration_path)
df_informed_taxi_duration['date_time_origin'] = pd.to_datetime(df_informed_taxi_duration['date_time_origin'])
df_informed_taxi_duration['date_time_destination'] = pd.to_datetime(df_informed_taxi_duration['date_time_destination'])
gdf_computed_taxi_duration = gpd.read_file(computed_duration_path)

list_taxi_informed_route_duration = []
for index, informed_taxi_duration in df_informed_taxi_duration.iterrows():
    duration = (informed_taxi_duration['date_time_destination']-informed_taxi_duration['date_time_origin']).total_seconds()/60
    list_taxi_informed_route_duration.append(duration)

list_taxi_computed_route_duration = gdf_computed_taxi_duration['duration'].tolist()
list_taxi_computed_route_duration = [duration/60 for duration in list_taxi_computed_route_duration]

print len(list_taxi_computed_route_duration)
print len(list_taxi_informed_route_duration)

for index in range(len(list_taxi_computed_route_duration)):
    if list_taxi_computed_route_duration[index] > max_showed_duration:
        list_taxi_computed_route_duration[index] = max_showed_duration

for index in range(len(list_taxi_informed_route_duration)):
    if list_taxi_informed_route_duration[index] > max_showed_duration:
        list_taxi_informed_route_duration[index] = max_showed_duration

list_taxi_computed_route_duration.sort()
ecdf_computed_duration = ECDF(list_taxi_computed_route_duration)

list_taxi_informed_route_duration.sort()
ecdf_informed_duration = ECDF(list_taxi_informed_route_duration)

fig, ax = plt.subplots()
plt.plot(ecdf_computed_duration.x, ecdf_computed_duration.y, label='computed duration')
plt.plot(ecdf_informed_duration.x, ecdf_informed_duration.y, label='informed duration')

#ax.xaxis.set_major_locator(ticker.MultipleLocator(60)) # set x sticks interal
plt.grid()
plt.legend()
ax.set_title('Taxi Trips on Sunday')
ax.set_xlabel('Travel Duration in Minutes')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(chart_name)
