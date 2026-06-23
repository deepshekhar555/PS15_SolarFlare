import pandas as pd
from pathlib import Path

combined_path = Path('D:/PS15_SolarFlare/Solar Low Energy X-ray Spectrometer/output/solexs_combined.csv')
window_start = pd.Timestamp('2026-06-06T13:40:00+00:00')
window_end = pd.Timestamp('2026-06-06T14:28:00+00:00')

df = pd.read_csv(combined_path)
df['DATETIME'] = pd.to_datetime(df['TIME'], unit='s', origin='unix', utc=True)
df = df.sort_values('DATETIME').reset_index(drop=True)
df['COUNTS'] = pd.to_numeric(df['COUNTS'], errors='coerce')
roll_win = 600
roll_med = df['COUNTS'].rolling(window=roll_win, min_periods=60, center=True).median()
roll_std = df['COUNTS'].rolling(window=roll_win, min_periods=60, center=True).std()
window = df[(df['DATETIME'] >= window_start) & (df['DATETIME'] <= window_end)].copy()
window['ROLL_MED'] = roll_med.loc[window.index].values
window['ROLL_STD'] = roll_std.loc[window.index].values
window['THRESH'] = window['ROLL_MED'] + 2.1 * window['ROLL_STD']
window['ABOVE'] = window['COUNTS'] > window['THRESH']

print('Window rows:', len(window))
print('Count above threshold:', int(window['ABOVE'].sum()))
print('\nFirst 20 rows:')
print(window[['DATETIME','COUNTS','ROLL_MED','ROLL_STD','THRESH','ABOVE']].head(20).to_string(index=False))
print('\nPeak rows around 14:01:00:')
peak_time = pd.Timestamp('2026-06-06T14:01:00+00:00')
peak_rows = window[(window['DATETIME'] >= peak_time - pd.Timedelta(seconds=20)) & (window['DATETIME'] <= peak_time + pd.Timedelta(seconds=20))]
print(peak_rows[['DATETIME','COUNTS','ROLL_MED','ROLL_STD','THRESH','ABOVE']].to_string(index=False))
print('\nLast 20 rows:')
print(window[['DATETIME','COUNTS','ROLL_MED','ROLL_STD','THRESH','ABOVE']].tail(20).to_string(index=False))
segments=[]
current=None
for _, row in window.iterrows():
    if row['ABOVE']:
        if current is None:
            current=[row['DATETIME'], row['DATETIME']]
        else:
            current[1]=row['DATETIME']
    else:
        if current is not None:
            segments.append(tuple(current))
            current=None
if current is not None:
    segments.append(tuple(current))
print('\nSegments where counts > threshold:')
if not segments:
    print('None')
else:
    for s,e in segments:
        print(f'{s} to {e}, duration {(e-s).total_seconds()+1}s')
