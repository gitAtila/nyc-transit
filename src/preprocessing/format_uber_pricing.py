'''
    Read uber pricing data and format it
'''

from sys import argv
import pandas as pd

uber_pricing_path = argv[1]
result_path = argv[2]

df_uber_pricing = pd.read_csv(uber_pricing_path)

print df_uber_pricing
