'''
    Vary cost policies and evaluate matchings
'''

from sys import argv
import pandas as pd

import matplotlib.pyplot as plt
from statsmodels.distributions.empirical_distribution import ECDF

max_benefit_05_05_05_path = argv[1]
max_benefit_1_05_05_path = argv[2]
max_benefit_1_1_05_path = argv[3]
max_benefit_1_1_1_path = argv[4]

extra_cost_chart_path = argv[5]
saving_money_chart_path = argv[6]

def extra_cost_saving_money(df_max_benefit):
    list_transit_passenger_extra_cost = []
    list_taxi_passenger_saving_money = []

    for index, max_benefit_trip in df_max_benefit.iterrows():
        list_transit_passenger_extra_cost.append(max_benefit_trip['transit_shared_cost'])
        list_taxi_passenger_saving_money.append(max_benefit_trip['taxi_private_cost'] - max_benefit_trip['taxi_shared_cost'])

    return list_transit_passenger_extra_cost, list_taxi_passenger_saving_money

df_max_benefit_05_05_05 = pd.read_csv(max_benefit_05_05_05_path)
df_max_benefit_1_05_05 = pd.read_csv(max_benefit_1_05_05_path)
df_max_benefit_1_1_05 = pd.read_csv(max_benefit_1_1_05_path)
df_max_benefit_1_1_1 = pd.read_csv(max_benefit_1_1_1_path)

print len(df_max_benefit_05_05_05)
print len(df_max_benefit_1_05_05)
print len(df_max_benefit_1_1_05)
print len(df_max_benefit_1_1_1)

# how much money did transit passengers pay more?
# how much money did taxi passengers saved?
list_extra_cost_05_05_05, list_saving_money_05_05_05 = extra_cost_saving_money(df_max_benefit_05_05_05)
list_extra_cost_1_05_05, list_saving_money_1_05_05 = extra_cost_saving_money(df_max_benefit_1_05_05)
list_extra_cost_1_1_05, list_saving_money_1_1_05 = extra_cost_saving_money(df_max_benefit_1_1_05)
list_extra_cost_1_1_1, list_saving_money_1_1_1 = extra_cost_saving_money(df_max_benefit_1_1_1)

'''
    Extra costs
'''

list_extra_cost_05_05_05.sort()
list_extra_cost_1_05_05.sort()
list_extra_cost_1_1_05.sort()
list_extra_cost_1_1_1.sort()

ecdf_extra_cost_05_05_05 = ECDF(list_extra_cost_05_05_05)
ecdf_extra_cost_1_05_05 = ECDF(list_extra_cost_1_05_05)
ecdf_extra_cost_1_1_05 = ECDF(list_extra_cost_1_1_05)
ecdf_extra_cost_1_1_1 = ECDF(list_extra_cost_1_1_1)

fig, ax = plt.subplots()
plt.plot(ecdf_extra_cost_05_05_05.x, ecdf_extra_cost_05_05_05.y, label='a=0.5 b=0.5 c=0.5')
plt.plot(ecdf_extra_cost_1_05_05.x, ecdf_extra_cost_1_05_05.y, label='a=1.0 b=0.5 c=0.5')
plt.plot(ecdf_extra_cost_1_1_05.x, ecdf_extra_cost_1_1_05.y, label='a=1.0 b=1.0 c=0.5')
plt.plot(ecdf_extra_cost_1_1_1.x, ecdf_extra_cost_1_1_1.y, label='a=1.0 b=1.0 c=1.0')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
plt.grid()
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('transit passenger sharing cost (dollars)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(extra_cost_chart_path)

'''
    Saving money
'''

list_saving_money_05_05_05.sort()
list_saving_money_1_05_05.sort()
list_saving_money_1_1_05.sort()
list_saving_money_1_1_1.sort()

ecdf_saving_money_05_05_05 = ECDF(list_saving_money_05_05_05)
ecdf_saving_money_1_05_05 = ECDF(list_saving_money_1_05_05)
ecdf_saving_money_1_1_05 = ECDF(list_saving_money_1_1_05)
ecdf_saving_money_1_1_1 = ECDF(list_saving_money_1_1_1)

fig, ax = plt.subplots()
plt.plot(ecdf_saving_money_05_05_05.x, ecdf_saving_money_05_05_05.y, label='a=0.5 b=0.5 c=0.5')
plt.plot(ecdf_saving_money_1_05_05.x, ecdf_saving_money_1_05_05.y, label='a=1.0 b=0.5 c=0.5')
plt.plot(ecdf_saving_money_1_1_05.x, ecdf_saving_money_1_1_05.y, label='a=1.0 b=1.0 c=0.5')
plt.plot(ecdf_saving_money_1_1_1.x, ecdf_saving_money_1_1_1.y, label='a=1.0 b=1.0 c=1.0')

# ax.xaxis.set_major_locator(ticker.MultipleLocator(20)) # set x sticks interal
plt.grid()
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('taxi passenger saving money (dollars)')
ax.set_ylabel('ECDF')
plt.tight_layout()
fig.savefig(saving_money_chart_path)
