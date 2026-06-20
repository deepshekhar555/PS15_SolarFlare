#!/usr/bin/env python3
"""Sweep HEL1OS sigma parameter to find optimal threshold."""
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMBINED_CSV = ROOT / 'output' / 'hel1os_combined.csv'

WINDOW_SECONDS = 600
MIN_SAMPLES = 3

df = pd.read_csv(COMBINED_CSV)
print(f'Data: {len(df):,} timesteps\n')

diffs = df['TIME'].diff().dropna()
non_zero_diffs = diffs[diffs > 0]
median_cadence = non_zero_diffs.median() if len(non_zero_diffs) > 0 else 1.0
window_samples = int(WINDOW_SECONDS / median_cadence)

print(f'Cadence: {median_cadence:.3f}s, Window: {window_samples} samples\n')

# Pre-calculate rolling stats once
df['ROLL_MED'] = df['COUNTS'].rolling(window=window_samples, center=True, min_periods=1).median()
df['ROLL_STD'] = df['COUNTS'].rolling(window=window_samples, center=True, min_periods=1).std()
df['ROLL_STD'] = df['ROLL_STD'].fillna(0)

sigma_values = [2.0, 1.5, 1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
results = []

for sigma in sigma_values:
    df['THRESH'] = df['ROLL_MED'] + sigma * df['ROLL_STD']
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

    # Filter by min_samples
    valid_events = 0
    for start, end in segments:
        num_samples = end - start + 1
        if num_samples >= MIN_SAMPLES:
            valid_events += 1

    results.append((sigma, len(segments), valid_events))
    print(f'sigma={sigma}: {len(segments):6d} segments → {valid_events:5d} events (min_samples={MIN_SAMPLES})')

print('\n' + '='*50)
print('Recommendation: Choose sigma with ~20-50 events')
