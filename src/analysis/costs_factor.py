'''
    Evaluate integration factor policy
'''

from sys import argv
import pandas as pd

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from statsmodels.distributions.empirical_distribution import ECDF
plt.rcParams.update({'font.size': 16})

detour_factor_path = argv[1]
result_path = argv[2]

df_detour_factor = pd.read_csv(detour_factor_path)

list_detours = df_detour_factor['detour_factor'].tolist()

#list_detours.sort()
list_detours = sorted(i for i in list_detours if i >= 0)

print min(list_detours), max(list_detours)

ecdf_detours = ECDF(list_detours)

fig, ax = plt.subplots()
plt.plot(ecdf_detours.x, ecdf_detours.y, label='f')

ax.xaxis.set_major_locator(ticker.MultipleLocator(5)) # set x sticks interal
plt.legend(loc=4)
# ax.set_title('saturday')
ax.set_xlabel('Taxi passenger costs (orig - new)/orig')
ax.set_ylabel('CDF')
plt.xticks([0.0,0.2,0.4,0.6,0.8,1.0])
plt.tight_layout()
fig.savefig(result_path + 'costs_prop_detour_factor.pdf')
