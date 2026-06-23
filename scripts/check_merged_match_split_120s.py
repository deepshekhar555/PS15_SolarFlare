import pandas as pd
from pathlib import Path

root = Path('D:/PS15_SolarFlare')
merged = pd.read_csv(root / 'output' / 'solexs_nowcast_catalog_merged_120s.csv')
matched = pd.read_csv(root / 'Solar Low Energy X-ray Spectrometer' / 'output' / 'matched_flares.csv')

merged['PEAK_TIME'] = pd.to_datetime(merged['PEAK_TIME'])
matched = matched.rename(columns={c: c.strip() for c in matched.columns})

if 'START_DT' in matched.columns and 'END_DT' in matched.columns:
    matched['START_DT'] = pd.to_datetime(matched['START_DT'])
    matched['END_DT'] = pd.to_datetime(matched['END_DT'])
elif 'START' in matched.columns and 'END' in matched.columns:
    matched['START_DT'] = pd.to_datetime(matched['START'])
    matched['END_DT'] = pd.to_datetime(matched['END'])
else:
    raise ValueError('matched_flares.csv missing START_DT/END_DT or START/END columns')

matched_counts = []
for idx, row in matched.iterrows():
    matches = merged[(merged['PEAK_TIME'] >= row['START_DT']) & (merged['PEAK_TIME'] <= row['END_DT'])]
    matched_counts.append((idx, len(matches), row['START_DT'], row['END_DT']))

split_flares = [item for item in matched_counts if item[1] > 1]
print('Flares with >1 merged event match (120s):', len(split_flares))
for idx, count, start, end in split_flares:
    print(f'  flare #{idx}: {count} merged events, window {start} to {end}')

matched_flare_count = sum(1 for _, count, _, _ in matched_counts if count > 0)
matched_event_count = merged['PEAK_TIME'].apply(lambda t: any((matched['START_DT'] <= t) & (t <= matched['END_DT']))).sum()
print('\nMatched flare totals (120s):')
print('  total matched flares:', matched_flare_count, 'of', len(matched))
print('  merged events matching flares:', matched_event_count)

matched_flag = merged['PEAK_TIME'].apply(lambda t: any((matched['START_DT'] <= t) & (t <= matched['END_DT'])))
unmatched = merged[~matched_flag]
print('\nUnmatched merged event count (120s):', len(unmatched))
