import pandas as pd
from pathlib import Path

ROOT = Path('D:/PS15_SolarFlare')
matched = pd.read_csv(ROOT / 'Solar Low Energy X-ray Spectrometer' / 'output' / 'matched_flares.csv')
nowcast = pd.read_csv(ROOT / 'Solar Low Energy X-ray Spectrometer' / 'output' / 'solexs_nowcast_catalog.csv')

matched['START_DT'] = pd.to_datetime(matched['START_DT'])
matched['END_DT'] = pd.to_datetime(matched['END_DT'])
nowcast['PEAK_TIME'] = pd.to_datetime(nowcast['PEAK_TIME'])

# Count nowcast events whose peak lies within any matched flare window.
nowcast_peak_matched = nowcast['PEAK_TIME'].apply(
    lambda peak: any((row.START_DT <= peak <= row.END_DT) for row in matched.itertuples())
)

# Count matched flare windows with at least one nowcast peak.
matched_flare_caught = 0
for mf in matched.itertuples():
    if any((mf.START_DT <= peak <= mf.END_DT) for peak in nowcast['PEAK_TIME']):
        matched_flare_caught += 1

# Count nowcast events with any overlap by window, not just peak.
nowcast_window_overlap = nowcast.apply(
    lambda nc: any((nc.START <= mf.END_DT and nc.END >= mf.START_DT) for mf in matched.itertuples()), axis=1
)

print('=== Matching logic consistency check ===')
print(f'Total nowcast events: {len(nowcast)}')
print(f'Nowcast events with peak in matched flare window: {nowcast_peak_matched.sum()}')
print(f'Nowcast events overlapping matched flare window: {nowcast_window_overlap.sum()}')
print(f'Unmatched nowcast events by peak matching: {len(nowcast) - nowcast_peak_matched.sum()}')
print(f'Unmatched nowcast events by window overlap: {len(nowcast) - nowcast_window_overlap.sum()}')
print(f'Total matched flare windows: {len(matched)}')
print(f'Matched flare windows containing >=1 nowcast peak: {matched_flare_caught}')
print('---')
print('Note: analyze_overlap_corrected.py reports 875 nowcast peaks inside matched windows and 68 matched flare windows caught.')
