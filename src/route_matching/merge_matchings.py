from sys import argv
import pandas as pd

df_csv_1 = pd.read_csv(argv[1])
df_csv_2 = pd.read_csv(argv[2])
df_csv_3 = pd.read_csv(argv[3])

frames = [df_csv_1, df_csv_2, df_csv_3]

df_result = pd.concat(frames)

df_result.to_csv(argv[4])
