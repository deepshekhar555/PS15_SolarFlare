import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path('D:/PS15_SolarFlare')
COMBINED = ROOT / 'Solar Low Energy X-ray Spectrometer' / 'output' / 'solexs_combined.csv'
OUT = ROOT / 'Solar Low Energy X-ray Spectrometer' / 'output' / 'solexs_20260610_2346_event.png'

start_plot = pd.to_datetime('2026-06-10T23:30:00Z')
end_plot = pd.to_datetime('2026-06-10T23:55:00Z')
shade_start = pd.to_datetime('2026-06-10T23:35:58Z')
shade_end = pd.to_datetime('2026-06-10T23:47:17Z')

# Load combined counts
df = pd.read_csv(COMBINED)
# TIME is Unix seconds
df['TIME_DT'] = pd.to_datetime(df['TIME'], unit='s', utc=True)
# Filter range
mask = (df['TIME_DT'] >= start_plot) & (df['TIME_DT'] <= end_plot)
plot_df = df.loc[mask].copy()
if plot_df.empty:
    raise SystemExit('No data points in requested plot range')

# Plot
plt.style.use('seaborn-v0_8')
fig, ax = plt.subplots(figsize=(10,4))
ax.plot(plot_df['TIME_DT'], plot_df['COUNTS'], label='SoLEXS COUNTS', color='C0')
ax.set_title('SoLEXS counts 2026-06-10 23:30–23:55 UTC')
ax.set_ylabel('Counts')
ax.set_xlabel('Time (UTC)')
# Shade detected event window
ax.axvspan(shade_start, shade_end, color='C1', alpha=0.3, label='Detected event window')
# Mark peak
peak_mask = (plot_df['TIME_DT'] >= shade_start) & (plot_df['TIME_DT'] <= shade_end)
if peak_mask.any():
    peak_row = plot_df.loc[peak_mask].iloc[plot_df.loc[peak_mask]['COUNTS'].argmax()]
    ax.axvline(peak_row['TIME_DT'], color='k', linestyle='--', linewidth=1)
    ax.text(peak_row['TIME_DT'], peak_row['COUNTS']+5, 'Peak', ha='center')

ax.legend()
fig.autofmt_xdate()
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=150, bbox_inches='tight')
print('Saved plot to', OUT)
