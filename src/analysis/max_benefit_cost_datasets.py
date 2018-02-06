'''
    Vary cost datasets and evaluate matchings
'''

from sys import argv
import pandas as pd

import matplotlib.pyplot as plt
from statsmodels.distributions.empirical_distribution import ECDF

max_benefit_real_path = argv[1]
max_benefit_10min_5x_path = argv[2]
max_benefit_10min_10x_path = argv[3]
max_benefit_20min_5x_path = argv[4]
max_benefit_20min_10x_path = argv[5]

extra_cost_chart_path = argv[6]
extra_money_chart_path = argv[7]
saving_money_chart_path = argv[8]

def extra_cost_saving_money(df_max_benefit):
    list_transit_passenger_extra_cost = []
    list_taxi_driver_extra_money = []
    list_taxi_passenger_saving_money = []

    for index, max_benefit_trip in df_max_benefit.iterrows():
        list_transit_passenger_extra_cost.append(max_benefit_trip['transit_shared_cost'])
        list_taxi_passenger_saving_money.append(max_benefit_trip['taxi_private_cost'] - max_benefit_trip['taxi_shared_cost'])
        list_taxi_driver_extra_money.append(max_benefit_trip['transit_shared_cost'] + max_benefit_trip['taxi_shared_cost']\
        - max_benefit_trip['taxi_private_cost'])

    return list_transit_passenger_extra_cost, list_taxi_driver_extra_money, list_taxi_passenger_saving_money

df_max_benefit_real = pd.read_csv(max_benefit_real_path)
df_max_benefit_10min_5x = pd.read_csv(max_benefit_10min_5x_path)
df_max_benefit_10min_10x = pd.read_csv(max_benefit_10min_10x_path)
df_max_benefit_20min_5x = pd.read_csv(max_benefit_20min_5x_path)
df_max_benefit_20min_10x = pd.read_csv(max_benefit_20min_10x_path)

print len(df_max_benefit_real)
print len(df_max_benefit_10min_5x)
print len(df_max_benefit_10min_10x)
print len(df_max_benefit_20min_5x)
print len(df_max_benefit_20min_10x)

# how much money did transit passengers pay more?
# how much money did taxi passengers saved?
list_extra_cost_real, list_extra_money_real, list_saving_money_real = extra_cost_saving_money(df_max_benefit_real)
list_extra_cost_10min_5x, list_extra_money_10min_5x,  list_saving_money_10min_5x = extra_cost_saving_money(df_max_benefit_10min_5x)
list_extra_cost_10min_10x, list_extra_money_10min_10x, list_saving_money_10min_10x = extra_cost_saving_money(df_max_benefit_10min_10x)
list_extra_cost_20min_5x, list_extra_money_20min_5x, list_saving_money_20min_5x = extra_cost_saving_money(df_max_benefit_20min_5x)
list_extra_cost_20min_10x, list_extra_money_20min_10x, list_saving_money_20min_10x = extra_cost_saving_money(df_max_benefit_20min_10x)

'''
    Extra costs
'''

list_extra_cost_real.sort()
list_extra_cost_10min_5x.sort()
list_extra_cost_10min_10x.sort()
list_extra_cost_20min_5x.sort()
list_extra_cost_20min_10x.sort()

ecdf_extra_cost_real = ECDF(list_extra_cost_real)
ecdf_extra_cost_10min_5x = ECDF(list_extra_cost_10min_5x)
ecdf_extra_cost_10min_10x = ECDF(list_extra_cost_10min_10x)
ecdf_extra_cost_20min_5x = ECDF(list_extra_cost_20min_5x)
ecdf_extra_cost_20min_10x = ECDF(list_extra_cost_20min_10x)

fig, ax = plt.subplots()
plt.plot(ecdf_extra_cost_real.x, ecdf_extra_cost_real.y, label='real')
plt.plot(ecdf_extra_cost_10min_5x.x, ecdf_extra_cost_10min_5x.y, label='10min_5x')
plt.plot(ecdf_extra_cost_10min_10x.x, ecdf_extra_cost_10min_10x.y, label='10min_10x')
plt.plot(ecdf_extra_cost_20min_5x.x, ecdf_extra_cost_20min_5x.y, label='20min_5x')
plt.plot(ecdf_extra_cost_20min_10x.x, ecdf_extra_cost_20min_10x.y, label='20min_10x')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
plt.grid()
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('transit passenger sharing cost (dollars)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(extra_cost_chart_path)

'''
    Extra money
'''

list_extra_money_real.sort()
list_extra_money_10min_5x.sort()
list_extra_money_10min_10x.sort()
list_extra_money_20min_5x.sort()
list_extra_money_20min_10x.sort()

ecdf_extra_money_real = ECDF(list_extra_money_real)
ecdf_extra_money_10min_5x = ECDF(list_extra_money_10min_5x)
ecdf_extra_money_10min_10x = ECDF(list_extra_money_10min_10x)
ecdf_extra_money_20min_5x = ECDF(list_extra_money_20min_5x)
ecdf_extra_money_20min_10x = ECDF(list_extra_money_20min_10x)

fig, ax = plt.subplots()
plt.plot(ecdf_extra_money_real.x, ecdf_extra_money_real.y, label='real')
plt.plot(ecdf_extra_money_10min_5x.x, ecdf_extra_money_10min_5x.y, label='10min_5x')
plt.plot(ecdf_extra_money_10min_10x.x, ecdf_extra_money_10min_10x.y, label='10min_10x')
plt.plot(ecdf_extra_money_20min_5x.x, ecdf_extra_money_20min_5x.y, label='20min_5x')
plt.plot(ecdf_extra_money_20min_10x.x, ecdf_extra_money_20min_10x.y, label='20min_10x')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
plt.grid()
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('taxi driver extra money (dollars)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(extra_money_chart_path)

'''
    Saving money
'''

list_saving_money_real.sort()
list_saving_money_10min_5x.sort()
list_saving_money_10min_10x.sort()
list_saving_money_20min_5x.sort()
list_saving_money_20min_10x.sort()

ecdf_saving_money_real = ECDF(list_saving_money_real)
ecdf_saving_money_10min_5x = ECDF(list_saving_money_10min_5x)
ecdf_saving_money_10min_10x = ECDF(list_saving_money_10min_10x)
ecdf_saving_money_20min_5x = ECDF(list_saving_money_20min_5x)
ecdf_saving_money_20min_10x = ECDF(list_saving_money_20min_10x)

fig, ax = plt.subplots()
plt.plot(ecdf_saving_money_real.x, ecdf_saving_money_real.y, label='real')
plt.plot(ecdf_saving_money_10min_5x.x, ecdf_saving_money_10min_5x.y, label='10min_5x')
plt.plot(ecdf_saving_money_10min_10x.x, ecdf_saving_money_10min_10x.y, label='10min_10x')
plt.plot(ecdf_saving_money_20min_5x.x, ecdf_saving_money_20min_5x.y, label='20min_5x')
plt.plot(ecdf_saving_money_20min_10x.x, ecdf_saving_money_20min_10x.y, label='20min_10x')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
plt.grid()
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('taxi passenger saving money (dollars)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(saving_money_chart_path)
