import pandas as pd
from pathlib import Path

base = Path('D:/PS15_SolarFlare/Solar Low Energy X-ray Spectrometer/output')
combined = pd.read_csv(base / 'solexs_combined.csv')
matched = pd.read_csv(base / 'matched_flares.csv')
nowcast = pd.read_csv(base / 'solexs_nowcast_catalog.csv')

print("=" * 80)
print("MATCHED_FLARES (first 5)")
print("=" * 80)
print(matched[['DATE', 'START', 'PEAK', 'END', 'CLASS']].head(5).to_string(index=False))

print("\n" + "=" * 80)
print("NOWCAST (first 5)")
print("=" * 80)
print(nowcast[['START', 'PEAK_TIME', 'END']].head(5).to_string(index=False))

print("\n" + "=" * 80)
print("COMBINED DATA DATETIME RANGE")
print("=" * 80)
combined['DATETIME'] = pd.to_datetime(combined['TIME'], unit='s', origin='unix', utc=True)
print(f"MIN: {combined['DATETIME'].min()}")
print(f"MAX: {combined['DATETIME'].max()}")
print(f"Total rows: {len(combined)}")

# Check for time overlap between first matched event and first 3 nowcasts
print("\n" + "=" * 80)
print("OVERLAP CHECK: First Matched Event vs First 3 Nowcast Events")
print("=" * 80)
first_matched_start = pd.to_datetime(matched.iloc[0]['START_DT'])
first_matched_end = pd.to_datetime(matched.iloc[0]['END_DT'])
first_matched_peak = pd.to_datetime(matched.iloc[0]['PEAK_DT'])
print(f"First matched event: START={first_matched_start}, PEAK={first_matched_peak}, END={first_matched_end}")

for i in range(min(3, len(nowcast))):
    nc_start = pd.to_datetime(nowcast.iloc[i]['START'])
    nc_end = pd.to_datetime(nowcast.iloc[i]['END'])
    nc_peak = pd.to_datetime(nowcast.iloc[i]['PEAK_TIME'])
    overlaps = (nc_start <= first_matched_peak <= nc_end) or (first_matched_start <= nc_peak <= first_matched_end)
    print(f"  Nowcast {i}: START={nc_start}, PEAK={nc_peak}, END={nc_end}, Overlaps={overlaps}")

# Check if all matched times fall within combined datetime range
print("\n" + "=" * 80)
print("TIME RANGE VALIDATION")
print("=" * 80)
combined_min = combined['DATETIME'].min()
combined_max = combined['DATETIME'].max()
matched_starts = pd.to_datetime(matched['START_DT'])
matched_in_range = (matched_starts >= combined_min) & (matched_starts <= combined_max)
print(f"Matched events with START in combined range: {matched_in_range.sum()} / {len(matched)}")
print(f"Combined range: {combined_min} to {combined_max}")
print(f"First matched START: {matched_starts.min()}")
print(f"Last matched START: {matched_starts.max()}")
