import pandas as pd
from pathlib import Path

combined_path = Path('D:/PS15_SolarFlare/Solar Low Energy X-ray Spectrometer/output/solexs_combined.csv')

# load data
ndf = pd.read_csv(combined_path)
df = ndf.sort_values('TIME').reset_index(drop=True)
df['DATETIME'] = pd.to_datetime(df['TIME'], unit='s', origin='unix', utc=True)
df['COUNTS'] = pd.to_numeric(df['COUNTS'], errors='coerce')

WINDOW = 600
SIGMA = 2.1

# centered baseline (current code)
df['ROLL_MED_CENTER'] = df['COUNTS'].rolling(window=WINDOW, min_periods=60, center=True).median()
df['ROLL_STD_CENTER'] = df['COUNTS'].rolling(window=WINDOW, min_periods=60, center=True).std()
df['TH_CENTER'] = df['ROLL_MED_CENTER'] + SIGMA * df['ROLL_STD_CENTER']

# causal baseline using past data only
# shift by 1 so threshold at t does not include current sample
df['ROLL_MED_PAST'] = df['COUNTS'].shift(1).rolling(window=WINDOW, min_periods=60).median()
df['ROLL_STD_PAST'] = df['COUNTS'].shift(1).rolling(window=WINDOW, min_periods=60).std()
df['TH_PAST'] = df['ROLL_MED_PAST'] + SIGMA * df['ROLL_STD_PAST']

window = df[(df['DATETIME'] >= '2026-06-06T13:40:00+00:00') & (df['DATETIME'] <= '2026-06-06T14:28:00+00:00')].copy()
window['ABOVE_CENTER'] = window['COUNTS'] > window['TH_CENTER']
window['ABOVE_PAST'] = window['COUNTS'] > window['TH_PAST']

print('Window rows:', len(window))
print('Above threshold (centered):', int(window['ABOVE_CENTER'].sum()))
print('Above threshold (past-only):', int(window['ABOVE_PAST'].sum()))

for label in ['CENTER', 'PAST']:
    segs = []
    current = None
    for _, row in window.iterrows():
        if row[f'ABOVE_{label}']:
            if current is None:
                current = [row['DATETIME'], row['DATETIME']]
            else:
                current[1] = row['DATETIME']
        else:
            if current is not None:
                segs.append(tuple(current))
                current = None
    if current is not None:
        segs.append(tuple(current))
    print(f'\nSegments for {label}: {len(segs)}')
    for seg in segs[:10]:
        print(f'  {seg[0]} to {seg[1]}, duration {int((seg[1]-seg[0]).total_seconds()+1)}s')

peak = window[(window['DATETIME'] >= '2026-06-06T14:00:40+00:00') & (window['DATETIME'] <= '2026-06-06T14:01:20+00:00')]
print('\nPeak sample comparison:')
print(peak[['DATETIME','COUNTS','TH_CENTER','TH_PAST','ABOVE_CENTER','ABOVE_PAST']].to_string(index=False))
