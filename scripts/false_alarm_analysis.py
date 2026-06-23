import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Solar Low Energy X-ray Spectrometer' / 'output'

matched = pd.read_csv(OUT / 'matched_flares.csv')
nowcast = pd.read_csv(OUT / 'solexs_nowcast_catalog.csv')

matched['START_DT'] = pd.to_datetime(matched['START_DT'])
matched['END_DT'] = pd.to_datetime(matched['END_DT'])
nowcast['PEAK_TIME'] = pd.to_datetime(nowcast['PEAK_TIME'])
nowcast['START'] = pd.to_datetime(nowcast['START'])
nowcast['END'] = pd.to_datetime(nowcast['END'])
nowcast['PEAK_COUNTS'] = pd.to_numeric(nowcast['PEAK_COUNTS'], errors='coerce')
nowcast['DURATION_s'] = pd.to_numeric(nowcast['DURATION_s'], errors='coerce')

# Identify unmatched events by whether peak falls in any matched flare window.
matched_intervals = list(zip(matched['START_DT'], matched['END_DT']))

unmatched = []
for _, nc in nowcast.iterrows():
    peak = nc['PEAK_TIME']
    matched_peak = any(start <= peak <= end for start, end in matched_intervals)
    if not matched_peak:
        unmatched.append(nc)
unmatched = pd.DataFrame(unmatched)

print('FALSE ALARM ANALYSIS')
print('====================')
print(f'Total nowcast events: {len(nowcast):,}')
print(f'Known matched flares: {len(matched):,}')
print(f'Unmatched nowcast events: {len(unmatched):,}')
print()

if unmatched.empty:
    print('No unmatched events to analyze.')
    raise SystemExit(0)

# Binning strategy
count_bins = [0, 300, 600, 900, 1200, 999999]
count_labels = ['very low', 'low', 'medium', 'high', 'very high']
unmatched['PEAK_BIN'] = pd.cut(unmatched['PEAK_COUNTS'], bins=count_bins, labels=count_labels, right=False)

duration_bins = [0, 5, 15, 60, 300, 999999]
duration_labels = ['very short', 'short', 'medium', 'long', 'very long']
unmatched['DURATION_BIN'] = pd.cut(unmatched['DURATION_s'], bins=duration_bins, labels=duration_labels, right=False)

print('Peak counts distribution (unmatched):')
print(unmatched['PEAK_BIN'].value_counts().sort_index().to_string())
print()
print('Duration distribution (unmatched):')
print(unmatched['DURATION_BIN'].value_counts().sort_index().to_string())
print()
print('Peak counts vs Duration cross-tab:')
print(pd.crosstab(unmatched['PEAK_BIN'], unmatched['DURATION_BIN'], margins=True))
print()
print('Summary statistics for unmatched events:')
print(unmatched[['PEAK_COUNTS', 'DURATION_s']].describe().to_string())
print()
print('Top 20 unmatched by PEAK_COUNTS:')
print(unmatched.sort_values('PEAK_COUNTS', ascending=False)[['PEAK_TIME', 'PEAK_COUNTS', 'DURATION_s']].head(20).to_string(index=False))
print()
print('Top 20 unmatched by DURATION_s:')
print(unmatched.sort_values('DURATION_s', ascending=False)[['PEAK_TIME', 'PEAK_COUNTS', 'DURATION_s']].head(20).to_string(index=False))
print()
print('Low-amplitude, short-duration false alarms:')
low_short = unmatched[(unmatched['PEAK_COUNTS'] < 300) & (unmatched['DURATION_s'] < 15)]
print(f'  Count: {len(low_short):,}')
print(low_short[['PEAK_TIME', 'PEAK_COUNTS', 'DURATION_s']].head(20).to_string(index=False))
