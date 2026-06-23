import pandas as pd
from pathlib import Path

ROOT = Path('D:/PS15_SolarFlare')
SOLEXS_NOWCAST = ROOT / 'Solar Low Energy X-ray Spectrometer' / 'output' / 'solexs_nowcast_catalog.csv'
MERGED_OUTPUT = ROOT / 'output' / 'solexs_nowcast_catalog_merged.csv'
MATCHED = ROOT / 'Solar Low Energy X-ray Spectrometer' / 'output' / 'matched_flares.csv'
MERGE_GAP_SECONDS = 60

# Load catalogs
solexs = pd.read_csv(SOLEXS_NOWCAST)
matched = pd.read_csv(MATCHED)

# Parse datetimes
for col in ['START', 'END', 'PEAK_TIME']:
    solexs[col] = pd.to_datetime(solexs[col])

matched['START_DT'] = pd.to_datetime(matched['START_DT'])
matched['END_DT'] = pd.to_datetime(matched['END_DT'])

# Ensure numeric
solexs['PEAK_COUNTS'] = pd.to_numeric(solexs['PEAK_COUNTS'], errors='coerce')
solexs['DURATION_s'] = pd.to_numeric(solexs['DURATION_s'], errors='coerce')
solexs['SAMPLES'] = pd.to_numeric(solexs['SAMPLES'], errors='coerce')

# Sort by start time
solexs = solexs.sort_values('START').reset_index(drop=True)

merged_rows = []
current = None

def finalize(row):
    if row is None:
        return None
    return {
        'START': row['START'].isoformat(),
        'END': row['END'].isoformat(),
        'PEAK_TIME': row['PEAK_TIME'].isoformat(),
        'PEAK_COUNTS': float(row['PEAK_COUNTS']),
        'DURATION_s': float((row['END'] - row['START']).total_seconds()),
        'SAMPLES': int(row['SAMPLES']),
    }

for _, event in solexs.iterrows():
    if current is None:
        current = event.copy()
        continue

    gap = (event['START'] - current['END']).total_seconds()
    if gap <= MERGE_GAP_SECONDS:
        current['END'] = max(current['END'], event['END'])
        current['SAMPLES'] = int(current['SAMPLES'] + event['SAMPLES'])
        if event['PEAK_COUNTS'] > current['PEAK_COUNTS']:
            current['PEAK_COUNTS'] = event['PEAK_COUNTS']
            current['PEAK_TIME'] = event['PEAK_TIME']
    else:
        merged_rows.append(finalize(current))
        current = event.copy()

if current is not None:
    merged_rows.append(finalize(current))

merged = pd.DataFrame(merged_rows)
merged.to_csv(MERGED_OUTPUT, index=False)

# Analyze merged events against matched flares
merged['PEAK_TIME'] = pd.to_datetime(merged['PEAK_TIME'])

def peak_matches_flare(peak):
    return any(start <= peak <= end for start, end in zip(matched['START_DT'], matched['END_DT']))

merged['MATCHED'] = merged['PEAK_TIME'].apply(peak_matches_flare)

matched_flare_caught = 0
for start, end in zip(matched['START_DT'], matched['END_DT']):
    if any((merged['PEAK_TIME'] >= start) & (merged['PEAK_TIME'] <= end)):
        matched_flare_caught += 1

print('Merged SoLEXS nowcast catalog results')
print('===================================')
print(f'Total original events: {len(solexs):,}')
print(f'Total merged events: {len(merged):,}')
print(f'Matched real flare windows caught: {matched_flare_caught} / {len(matched):,}')
print(f'Matched merged nowcast events: {merged[merged["MATCHED"]].shape[0]:,}')
print(f'Unmatched merged events: {merged[~merged["MATCHED"]].shape[0]:,}')
print(f'False alarm rate (merged): {merged[~merged["MATCHED"]].shape[0] / len(merged):.3f}')
print('\nTop merged unmatched events by PEAK_COUNTS:')
print(merged[~merged['MATCHED']].sort_values('PEAK_COUNTS', ascending=False)[['PEAK_TIME', 'PEAK_COUNTS', 'DURATION_s']].head(20).to_string(index=False))

print('\nMerged event duration distribution:')
print(merged['DURATION_s'].describe().to_string())
print('\nMerged unmatched duration distribution:')
print(merged[~merged['MATCHED']]['DURATION_s'].describe().to_string())
