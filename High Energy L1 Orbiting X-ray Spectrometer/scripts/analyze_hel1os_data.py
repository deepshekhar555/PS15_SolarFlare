import pandas as pd

df = pd.read_csv('output/hel1os_combined.csv')
zeros = (df['COUNTS'] == 0).sum()
print(f'Zero counts: {zeros} / {len(df)} = {100*zeros/len(df):.1f}%')

nz = df[df['COUNTS'] > 0]
print(f'\nNon-zero stats:')
print(f'  count: {len(nz)}')
print(f'  min: {nz["COUNTS"].min()}')
print(f'  max: {nz["COUNTS"].max()}')
print(f'  mean: {nz["COUNTS"].mean():.2f}')
print(f'  median: {nz["COUNTS"].median():.2f}')
