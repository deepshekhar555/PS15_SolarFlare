#!/usr/bin/env python3
"""Merge SoLEXS and HEL1OS nowcast catalogs into combined detection catalog."""
import pandas as pd
from pathlib import Path

# ===== SETTINGS =====
SOLEXS_ROOT = Path('d:/PS15_SolarFlare/Solar Low Energy X-ray Spectrometer')
HELOS_ROOT = Path('d:/PS15_SolarFlare/High Energy L1 Orbiting X-ray Spectrometer')
OUTPUT_ROOT = Path('d:/PS15_SolarFlare')

SOLEXS_CATALOG = SOLEXS_ROOT / 'output' / 'solexs_nowcast_catalog.csv'
HELOS_CATALOG = HELOS_ROOT / 'output' / 'hel1os_nowcast_catalog.csv'
MERGED_OUTPUT = OUTPUT_ROOT / 'output' / 'solexs_hel1os_combined_catalog.csv'

MERGE_WINDOW_S = 120  # ±2 minutes to consider events as same

MERGED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

print(f'Loading SoLEXS: {SOLEXS_CATALOG}')
solexs = pd.read_csv(SOLEXS_CATALOG)
print(f'  {len(solexs)} events')

print(f'Loading HEL1OS: {HELOS_CATALOG}')
helos = pd.read_csv(HELOS_CATALOG)
print(f'  {len(helos)} events')

# Ensure numeric types
for col in ['PEAK_TIME', 'START_TIME', 'END_TIME', 'PEAK_COUNTS']:
    if col in solexs.columns:
        solexs[col] = pd.to_numeric(solexs[col], errors='coerce')
    if col in helos.columns:
        helos[col] = pd.to_numeric(helos[col], errors='coerce')

# Add instrument label
solexs['INSTRUMENT'] = 'SoLEXS'
helos['INSTRUMENT'] = 'HEL1OS'

# Rename columns to match for merging
solexs_cols = solexs.columns.tolist()
helos_cols = helos.columns.tolist()

# Standardize column names
solexs = solexs.rename(columns={
    'START_TIME': 'START_TIME',
    'END_TIME': 'END_TIME',
    'PEAK_TIME': 'PEAK_TIME',
    'PEAK_COUNTS': 'PEAK_COUNTS'
})

helos = helos.rename(columns={
    'START_TIME': 'START_TIME',
    'END_TIME': 'END_TIME',
    'PEAK_TIME': 'PEAK_TIME',
    'PEAK_COUNTS': 'PEAK_COUNTS'
})

# Combine all events
all_events = pd.concat([solexs, helos], ignore_index=True)
all_events = all_events.sort_values('PEAK_TIME').reset_index(drop=True)

print(f'\nTotal events before merging: {len(all_events)}')

# Merge close events (same flare detected by both instruments)
merged_events = []
used = set()

for i, event_a in all_events.iterrows():
    if i in used:
        continue
    
    # Find all events within merge window
    close_events = []
    for j, event_b in all_events.iterrows():
        if j <= i or j in used:
            continue
        time_diff = abs(event_b['PEAK_TIME'] - event_a['PEAK_TIME'])
        if time_diff <= MERGE_WINDOW_S:
            close_events.append(j)
        elif time_diff > MERGE_WINDOW_S:
            break  # Sorted by PEAK_TIME, so no more close events
    
    if close_events:
        # Merge events from both instruments
        merged_row = event_a.copy()
        instruments = [event_a['INSTRUMENT']]
        peak_times = [event_a['PEAK_TIME']]
        peak_counts = [event_a['PEAK_COUNTS']]
        
        for j in close_events:
            event_b = all_events.iloc[j]
            instruments.append(event_b['INSTRUMENT'])
            peak_times.append(event_b['PEAK_TIME'])
            peak_counts.append(event_b['PEAK_COUNTS'])
            used.add(j)
        
        merged_row['INSTRUMENTS'] = '+'.join(instruments)
        merged_row['NUM_INSTRUMENTS'] = len(set(instruments))
        merged_row['PEAK_TIME_DELTA_S'] = max(peak_times) - min(peak_times)
        used.add(i)
        merged_events.append(merged_row)
    else:
        # Standalone event
        row = event_a.copy()
        row['INSTRUMENTS'] = event_a['INSTRUMENT']
        row['NUM_INSTRUMENTS'] = 1
        row['PEAK_TIME_DELTA_S'] = 0
        used.add(i)
        merged_events.append(row)

merged_df = pd.DataFrame(merged_events)

print(f'After merging: {len(merged_df)} unique events')
print(f'\nMerge breakdown:')
print(f'  SoLEXS-only: {(merged_df["INSTRUMENTS"] == "SoLEXS").sum()}')
print(f'  HEL1OS-only: {(merged_df["INSTRUMENTS"] == "HEL1OS").sum()}')
print(f'  Both instruments: {(merged_df["NUM_INSTRUMENTS"] == 2).sum()}')

# Select useful columns and sort
output_cols = ['INSTRUMENTS', 'NUM_INSTRUMENTS', 'PEAK_TIME', 'PEAK_TIME_DELTA_S', 
               'PEAK_COUNTS', 'START_TIME', 'END_TIME', 'DURATION_s', 'SAMPLES']
output_cols = [c for c in output_cols if c in merged_df.columns]
merged_df = merged_df[output_cols].sort_values('PEAK_TIME').reset_index(drop=True)

merged_df.to_csv(MERGED_OUTPUT, index=False)
print(f'\n✅ Saved combined catalog to: {MERGED_OUTPUT}')
print(f'   {len(merged_df)} events total')
