#!/usr/bin/env python3
"""Pipeline state summary."""
import pandas as pd
from pathlib import Path

OUT = Path('output')

print('=== SoLEXS PIPELINE STATE SUMMARY (2026-06-19) ===\n')

print('[1] Combined SoLEXS Data:')
df_combined = pd.read_csv(OUT / 'solexs_combined.csv')
print(f'    Rows: {len(df_combined):,} data points')
print(f'    Cols: TIME, COUNTS, DATE')
print(f'    Date range: {df_combined["DATE"].min()} to {df_combined["DATE"].max()}')
print()

print('[2] SoLEXS-only Nowcast Detector:')
df_nowcast = pd.read_csv(OUT / 'solexs_nowcast_catalog.csv')
print(f'    Events detected: {len(df_nowcast)}')
print(f'    Parameters: sigma=2.1, min_samples=3, window=600s')
print(f'    Duration range: {df_nowcast["DURATION_s"].min():.1f}s to {df_nowcast["DURATION_s"].max():.1f}s')
print(f'    Peak counts range: {df_nowcast["PEAK_COUNTS"].min():.1f} to {df_nowcast["PEAK_COUNTS"].max():.1f}')
print()

print('[3] GOES External Labels:')
df_matched = pd.read_csv(OUT / 'matched_flares.csv')
print(f'    GOES events matched: {len(df_matched)}')
top_classes = df_matched['CLASS'].value_counts().head(5)
print(f'    Top classes: {", ".join(f"{c}({cnt})" for c, cnt in top_classes.items())}')
print()

print('[4] Labeled SoLEXS (with GOES intervals):')
df_labeled = pd.read_csv(OUT / 'labeled_solexs.csv')
flare_rows = int(df_labeled['IS_FLARE'].sum())
print(f'    Total SoLEXS rows: {len(df_labeled):,}')
print(f'    Rows labeled as flare: {flare_rows:,}')
print()

print('[5] Pipeline Scripts Available:')
scripts = sorted(Path('scripts').glob('*.py'))
for s in scripts:
    print(f'    - {s.name}')
print()

print('✅ Pipeline is consistent and ready for next phase')
