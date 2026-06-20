import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Prefer labeled file (has DATETIME and IS_FLARE); fall back to combined
OUT = Path('D:/PS15_SolarFlare/output')
LABELED = OUT / 'labeled_solexs.csv'
COMBINED = OUT / 'solexs_combined.csv'

if LABELED.exists():
    df = pd.read_csv(LABELED, parse_dates=['DATETIME'])
    print(f"Loaded labeled SoLEXS: {len(df)} rows")
else:
    df = pd.read_csv(COMBINED)
    # create a DATETIME if missing
    df['DATETIME'] = pd.to_datetime(df['TIME'], unit='s', origin='unix', utc=True)
    print(f"Loaded combined SoLEXS: {len(df)} rows (no labels)")

# Ensure counts numeric
df['COUNTS'] = pd.to_numeric(df['COUNTS'], errors='coerce')

# Compute rolling background (30 min)
window_seconds = 1800
roll_win = window_seconds
df = df.sort_values('DATETIME')
df['ROLL_MED'] = df['COUNTS'].rolling(window=roll_win, min_periods=60).median()
df['ROLL_STD'] = df['COUNTS'].rolling(window=roll_win, min_periods=60).std()
df['THRESH'] = df['ROLL_MED'] + 3.0 * df['ROLL_STD']

# Detection mask (if IS_FLARE exists use it for coloring)
if 'IS_FLARE' in df.columns:
    df['IS_FLARE'] = df['IS_FLARE'].astype(bool)
else:
    df['IS_FLARE'] = False

# Plot full time series with threshold (first date)
first_date = df['DATETIME'].dt.strftime('%Y%m%d').iloc[0]
sample = df[df['DATETIME'].dt.strftime('%Y%m%d') == first_date]
plt.figure(figsize=(15, 5))
plt.plot(sample['DATETIME'], sample['COUNTS'], color='orange', linewidth=0.5, label='COUNTS')
plt.plot(sample['DATETIME'], sample['ROLL_MED'], color='blue', linewidth=0.8, label='ROLL_MED')
plt.plot(sample['DATETIME'], sample['THRESH'], color='red', linestyle='--', linewidth=0.8, label='THRESH')
plt.scatter(sample[sample['IS_FLARE']]['DATETIME'], sample[sample['IS_FLARE']]['COUNTS'], s=4, color='red', label='Labeled flare')
plt.title(f'Aditya-L1 SoLEXS — {first_date}')
plt.xlabel('Time (UTC)')
plt.ylabel('X-ray Counts')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plot_path = OUT / f'solexs_plot_{first_date}.png'
plt.savefig(plot_path, dpi=150)
plt.close()
print(f"Saved: {plot_path}")

# Also save a zoom for a detected event if exists
detected = df[df['IS_FLARE']]
if not detected.empty:
    # pick first labeled flare interval
    first_idx = detected.index[0]
    center = df.loc[first_idx, 'DATETIME']
    s = center - pd.Timedelta(minutes=10)
    e = center + pd.Timedelta(minutes=10)
    zoom = df[(df['DATETIME'] >= s) & (df['DATETIME'] <= e)]
    plt.figure(figsize=(12,4))
    plt.plot(zoom['DATETIME'], zoom['COUNTS'], color='orange', linewidth=0.6)
    plt.plot(zoom['DATETIME'], zoom['ROLL_MED'], color='blue', linewidth=0.8)
    plt.plot(zoom['DATETIME'], zoom['THRESH'], color='red', linestyle='--', linewidth=0.8)
    plt.scatter(zoom[zoom['IS_FLARE']]['DATETIME'], zoom[zoom['IS_FLARE']]['COUNTS'], s=8, color='red')
    plt.title('Zoom on labeled flare')
    plt.xlabel('Time (UTC)')
    plt.ylabel('Counts')
    plt.tight_layout()
    zoom_path = OUT / 'solexs_plot_zoom.png'
    plt.savefig(zoom_path, dpi=150)
    plt.close()
    print(f"Saved: {zoom_path}")

print('Plotting complete')