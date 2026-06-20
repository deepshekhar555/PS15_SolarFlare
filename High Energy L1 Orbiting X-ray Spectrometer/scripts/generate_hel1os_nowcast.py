#!/usr/bin/env python3
"""Generate HEL1OS nowcast event catalog using rolling-threshold detection."""
import pandas as pd
import numpy as np
from pathlib import Path

# ===== SETTINGS =====
ROOT = Path(__file__).resolve().parents[1]
COMBINED_CSV = ROOT / 'output' / 'hel1os_combined.csv'
OUTPUT_CSV = ROOT / 'output' / 'hel1os_nowcast_catalog.csv'

# Detection parameters
WINDOW_SECONDS = 600  # 10-minute rolling window
SIGMA = 0.2           # Tuned for HEL1OS (lower than SoLEXS's 2.1 due to different instrument characteristics)
MIN_SAMPLES = 3       # Minimum samples to form an event

print(f'Loading {COMBINED_CSV}...')
df = pd.read_csv(COMBINED_CSV)
print(f'Loaded {len(df):,} timesteps')

# Calculate actual cadence
diffs = df['TIME'].diff().dropna()
non_zero_diffs = diffs[diffs > 0]
if len(non_zero_diffs) > 0:
    median_cadence = non_zero_diffs.median()
    print(f'Median cadence: {median_cadence:.3f}s')
else:
    median_cadence = 1.0
    print(f'Warning: Could not determine cadence, using default 1.0s')

# Calculate window size in samples
window_samples = int(WINDOW_SECONDS / median_cadence)
print(f'Window: {WINDOW_SECONDS}s = ~{window_samples} samples')

print('\nCalculating rolling statistics...')
df['ROLL_MED'] = df['COUNTS'].rolling(window=window_samples, center=True, min_periods=1).median()
df['ROLL_STD'] = df['COUNTS'].rolling(window=window_samples, center=True, min_periods=1).std()
df['THRESH'] = df['ROLL_MED'] + SIGMA * df['ROLL_STD']
df['THRESH'] = df['THRESH'].fillna(df['ROLL_MED'])

print('Applying threshold...')
mask = df['COUNTS'] > df['THRESH']

# Find contiguous segments
segments = []
in_segment = False
start_idx = None

for i in range(len(df)):
    if mask.iloc[i]:
        if not in_segment:
            start_idx = i
            in_segment = True
    else:
        if in_segment:
            segments.append((start_idx, i - 1))
            in_segment = False

if in_segment:
    segments.append((start_idx, len(df) - 1))

print(f'Found {len(segments)} contiguous segments')

# Filter by min_samples and extract events
events = []
for start, end in segments:
    num_samples = end - start + 1
    if num_samples < MIN_SAMPLES:
        continue  # Too short

    segment_data = df.iloc[start:end+1]
    peak_idx = segment_data['COUNTS'].idxmax()
    peak_counts = segment_data.loc[peak_idx, 'COUNTS']
    peak_time = segment_data.loc[peak_idx, 'TIME']

    start_time = segment_data.iloc[0]['TIME']
    end_time = segment_data.iloc[-1]['TIME']
    duration_s = end_time - start_time

    events.append({
        'START_TIME': start_time,
        'END_TIME': end_time,
        'PEAK_TIME': peak_time,
        'PEAK_COUNTS': peak_counts,
        'DURATION_s': duration_s,
        'SAMPLES': num_samples,
    })

events_df = pd.DataFrame(events)
print(f'\n✅ Detected {len(events_df)} events (after min_samples={MIN_SAMPLES} filter)')

if len(events_df) > 0:
    print(f'Duration range: {events_df["DURATION_s"].min():.1f}s to {events_df["DURATION_s"].max():.1f}s')
    print(f'Peak counts range: {events_df["PEAK_COUNTS"].min():.1f} to {events_df["PEAK_COUNTS"].max():.1f}')

events_df.to_csv(OUTPUT_CSV, index=False)
print(f'\n✅ Saved to: {OUTPUT_CSV}')
print(f'Parameters: window={WINDOW_SECONDS}s, sigma={SIGMA}, min_samples={MIN_SAMPLES}')
