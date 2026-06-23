import pandas as pd
from pathlib import Path

base = Path('D:/PS15_SolarFlare/Solar Low Energy X-ray Spectrometer/output')
matched = pd.read_csv(base / 'matched_flares.csv')
nowcast = pd.read_csv(base / 'solexs_nowcast_catalog.csv')

print("=" * 80)
print("CORRECTED OVERLAP ANALYSIS")
print("=" * 80)

# Parse datetimes
matched['start_dt'] = pd.to_datetime(matched['START_DT'])
matched['end_dt'] = pd.to_datetime(matched['END_DT'])
matched['peak_dt'] = pd.to_datetime(matched['PEAK_DT'])

nowcast['start_dt'] = pd.to_datetime(nowcast['START'])
nowcast['end_dt'] = pd.to_datetime(nowcast['END'])
nowcast['peak_dt'] = pd.to_datetime(nowcast['PEAK_TIME'])

# Check 1: How many nowcast windows overlap ANY matched flare window?
nowcast_overlap_matched = 0
for _, nc in nowcast.iterrows():
    for _, mf in matched.iterrows():
        # Windows overlap if: nc_start < mf_end AND nc_end > mf_start
        if nc['start_dt'] < mf['end_dt'] and nc['end_dt'] > mf['start_dt']:
            nowcast_overlap_matched += 1
            break

# Check 2: How many nowcast peaks fall within matched flare windows?
nowcast_peaks_in_matched = 0
for _, nc in nowcast.iterrows():
    for _, mf in matched.iterrows():
        if mf['start_dt'] <= nc['peak_dt'] <= mf['end_dt']:
            nowcast_peaks_in_matched += 1
            break

# Check 3: How many matched flare windows contain nowcast peaks?
matched_contain_nowcast = 0
for _, mf in matched.iterrows():
    for _, nc in nowcast.iterrows():
        if mf['start_dt'] <= nc['peak_dt'] <= mf['end_dt']:
            matched_contain_nowcast += 1
            break

print(f"Total nowcast events: {len(nowcast)}")
print(f"Total matched flares: {len(matched)}")
print(f"\nNowcast windows that overlap ANY matched flare window: {nowcast_overlap_matched}")
print(f"Nowcast peaks falling within matched flare windows: {nowcast_peaks_in_matched}")
print(f"Matched flare windows containing at least one nowcast peak: {matched_contain_nowcast}")

# Sample the matching
print("\n" + "=" * 80)
print("DETAILED VIEW: First 3 Matched Flares + Their Nowcast Matches")
print("=" * 80)
for i, (_, mf) in enumerate(matched.head(3).iterrows()):
    print(f"\n[{i+1}] Matched Flare: {mf['START']}-{mf['END']} ({mf['CLASS']})")
    contained = []
    for _, nc in nowcast.iterrows():
        if mf['start_dt'] <= nc['peak_dt'] <= mf['end_dt']:
            contained.append(nc)
    if contained:
        print(f"    Contains {len(contained)} nowcast peak(s):")
        for nc in contained[:5]:
            print(f"      - {nc['PEAK_TIME']} (duration {(nc['end_dt']-nc['start_dt']).total_seconds()}s)")
    else:
        print(f"    Contains 0 nowcast peaks")
