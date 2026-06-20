import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
COMBINED = OUT / 'solexs_combined.csv'
NOWCAST = OUT / 'solexs_nowcast_catalog.csv'

def detect_nowcasts(combined_csv: Path, out_csv: Path, min_samples: int = 3, window_seconds: int = 600, sigma: float = 3.0):
    df = pd.read_csv(combined_csv)
    df['DATETIME'] = pd.to_datetime(df['TIME'], unit='s', origin='unix', utc=True)
    df = df.sort_values('DATETIME').reset_index(drop=True)
    df['COUNTS'] = pd.to_numeric(df['COUNTS'], errors='coerce')

    roll_win = window_seconds  # data is ~1 Hz so window_seconds ~ window samples
    df['ROLL_MED'] = df['COUNTS'].rolling(window=roll_win, min_periods=60, center=True).median()
    df['ROLL_STD'] = df['COUNTS'].rolling(window=roll_win, min_periods=60, center=True).std()
    df['THRESH'] = df['ROLL_MED'] + sigma * df['ROLL_STD']

    # Detection mask: counts strictly greater than threshold
    mask = df['COUNTS'] > df['THRESH']

    # Find contiguous runs of True in mask
    events = []
    in_event = False
    start_idx = None
    for i, val in enumerate(mask.fillna(False)):
        if val and not in_event:
            in_event = True
            start_idx = i
        elif not val and in_event:
            end_idx = i - 1
            in_event = False
            # record event
            seg = df.loc[start_idx:end_idx]
            samples = len(seg)
            if samples >= min_samples:
                start_dt = seg['DATETIME'].iloc[0]
                end_dt = seg['DATETIME'].iloc[-1]
                peak_row = seg.loc[seg['COUNTS'].idxmax()]
                peak_time = peak_row['DATETIME']
                peak_counts = float(peak_row['COUNTS'])
                duration = (end_dt - start_dt).total_seconds()
                events.append({
                    'START': start_dt.isoformat(),
                    'END': end_dt.isoformat(),
                    'PEAK_TIME': peak_time.isoformat(),
                    'PEAK_COUNTS': peak_counts,
                    'DURATION_s': duration,
                    'MAJORITY_CLASS': '',
                    'SAMPLES': samples,
                })
    # handle case where mask ends in event
    if in_event:
        seg = df.loc[start_idx:len(df)-1]
        samples = len(seg)
        if samples >= min_samples:
            start_dt = seg['DATETIME'].iloc[0]
            end_dt = seg['DATETIME'].iloc[-1]
            peak_row = seg.loc[seg['COUNTS'].idxmax()]
            peak_time = peak_row['DATETIME']
            peak_counts = float(peak_row['COUNTS'])
            duration = (end_dt - start_dt).total_seconds()
            events.append({
                'START': start_dt.isoformat(),
                'END': end_dt.isoformat(),
                'PEAK_TIME': peak_time.isoformat(),
                'PEAK_COUNTS': peak_counts,
                'DURATION_s': duration,
                'MAJORITY_CLASS': '',
                'SAMPLES': samples,
            })

    out_df = pd.DataFrame(events)
    out_df.to_csv(out_csv, index=False)
    print(f'Detected {len(out_df)} nowcast events (min_samples={min_samples}, window_s={window_seconds}, sigma={sigma})')


if __name__ == '__main__':
    if not COMBINED.exists():
        print(f'Missing combined CSV: {COMBINED}')
    else:
        detect_nowcasts(COMBINED, NOWCAST, min_samples=3, window_seconds=600, sigma=2.1)
