import pandas as pd
from pathlib import Path

combined_path = Path('D:/PS15_SolarFlare/Solar Low Energy X-ray Spectrometer/output/solexs_combined.csv')
window_start = pd.Timestamp('2026-06-06T13:40:00+00:00')
window_end = pd.Timestamp('2026-06-06T14:28:00+00:00')

# Load and compute exactly the same rolling baseline/threshold as generate_solexs_nowcast.py

df = pd.read_csv(combined_path)
df['DATETIME'] = pd.to_datetime(df['TIME'], unit='s', origin='unix', utc=True)
df = df.sort_values('DATETIME').reset_index(drop=True)
df['COUNTS'] = pd.to_numeric(df['COUNTS'], errors='coerce')
roll_win = 600
window = df[(df['DATETIME'] >= window_start) & (df['DATETIME'] <= window_end)].copy()
window['ROLL_MED'] = df['COUNTS'].rolling(window=roll_win, min_periods=60, center=True).median().loc[window.index].values
window['ROLL_STD'] = df['COUNTS'].rolling(window=roll_win, min_periods=60, center=True).std().loc[window.index].values
window['THRESH'] = window['ROLL_MED'] + 2.1 * window['ROLL_STD']
window['ABOVE'] = window['COUNTS'] > window['THRESH']

# Output key info
print('Window rows:', len(window))
print('Count above threshold:', window['ABOVE'].sum())
print('\nFirst 20 rows of the window:')
print(window[['DATETIME','COUNTS','ROLL_MED','ROLL_STD','THRESH','ABOVE']].head(20).to_string(index=False))
print('\nAround the flare peak:')
peak_time = pd.Timestamp('2026-06-06T14:01:00+00:00')
peak_rows = window[(window['DATETIME'] >= peak_time - pd.Timedelta(seconds=20)) & (window['DATETIME'] <= peak_time + pd.Timedelta(seconds=20))]
print(peak_rows[['DATETIME','COUNTS','ROLL_MED','ROLL_STD','THRESH','ABOVE']].to_string(index=False))
print('\nLast 20 rows of the window:')
print(window[['DATETIME','COUNTS','ROLL_MED','ROLL_STD','THRESH','ABOVE']].tail(20).to_string(index=False))

# Show any segments where ABOVE is True
above_segments = []
current = None
for _, row in window.iterrows():
    if row['ABOVE']:
        if current is None:
            current = [row['DATETIME'], row['DATETIME']]
        else:
            current[1] = row['DATETIME']
    else:
        if current is not None:
            above_segments.append(tuple(current))
            current = None
if current is not None:
    above_segments.append(tuple(current))

print('\nSegments where COUNTS > THRESH (if any):')
if not above_segments:
    print('None')
else:
    for seg in above_segments:
        duration = int((seg[1] - seg[0]).total_seconds() + 1)
        print(f'{seg[0]} to {seg[1]}, duration {duration}s')
