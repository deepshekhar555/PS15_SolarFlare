#!/usr/bin/env python3
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELED = ROOT / 'Solar Low Energy X-ray Spectrometer' / 'output' / 'labeled_solexs.csv'
COMBINED_CAT = ROOT / 'output' / 'solexs_hel1os_combined_catalog.csv'


def load_data():
    labeled = pd.read_csv(LABELED)
    if 'TIME' in labeled.columns:
        labeled['TIME_UNIX'] = pd.to_numeric(labeled['TIME'], errors='coerce')
        if labeled['TIME_UNIX'].isna().all() and 'DATETIME' in labeled.columns:
            labeled['TIME_UNIX'] = pd.to_datetime(labeled['DATETIME']).astype('int64') // 10**9
    else:
        labeled['TIME_UNIX'] = pd.to_datetime(labeled['DATETIME']).astype('int64') // 10**9
    labeled = labeled.sort_values('TIME_UNIX').reset_index(drop=True)
    return labeled


def get_flare_peaks(labeled):
    flare_peaks = []
    if COMBINED_CAT.exists():
        cc = pd.read_csv(COMBINED_CAT)
        if 'PEAK_TIME' in cc.columns:
            try:
                if cc['PEAK_TIME'].dtype == object:
                    peaks_unix = pd.to_datetime(cc['PEAK_TIME']).astype('int64') // 10**9
                else:
                    peaks_unix = pd.to_numeric(cc['PEAK_TIME'], errors='coerce')
                flare_peaks = peaks_unix.dropna().astype(int).values
            except Exception:
                flare_peaks = []
    if len(flare_peaks) == 0 and 'IS_FLARE' in labeled.columns:
        mask = labeled['IS_FLARE'] == 1
        if mask.any():
            labeled['grp'] = (mask != mask.shift(1)).cumsum()
            groups = labeled[mask].groupby('grp')
            flares = []
            for _, g in groups:
                idx = g['COUNTS'].idxmax()
                flare_time = g.loc[idx, 'TIME_UNIX']
                flares.append(flare_time)
            flare_peaks = np.array(flares, dtype=int)
    return flare_peaks


def make_windows(df, window_s=600, step_s=60):
    times = df['TIME_UNIX'].values
    counts = df['COUNTS'].values
    end_time = times[-1]
    start_time = times[0]
    windows = []
    for window_start in np.arange(start_time, end_time - window_s + 1, step_s):
        window_end = window_start + window_s
        mask = (times >= window_start) & (times < window_end)
        if not np.any(mask):
            continue
        vals = counts[mask]
        t_vals = times[mask]
        mean = np.mean(vals)
        std = np.std(vals)
        mx = np.max(vals)
        last = vals[-1]
        if len(t_vals) > 1:
            coeffs = np.polyfit(t_vals - t_vals[0], vals, 1)
            slope = coeffs[0]
        else:
            slope = 0.0
        windows.append({'start': window_start, 'end': window_end, 'mean': mean, 'std': std, 'max': mx, 'last': last, 'slope': slope})
    return pd.DataFrame(windows)


def label_windows(windows, flare_peaks_unix, horizon_s=1800):
    labels = []
    lead_times = []
    for _, row in windows.iterrows():
        end = row['end']
        window_peaks = flare_peaks_unix[(flare_peaks_unix > end) & (flare_peaks_unix <= end + horizon_s)]
        if len(window_peaks) > 0:
            labels.append(1)
            lead_times.append(window_peaks.min() - end)
        else:
            labels.append(0)
            lead_times.append(np.nan)
    windows['label'] = labels
    windows['lead_s'] = lead_times
    return windows


def main():
    labeled = load_data()
    flare_peaks = get_flare_peaks(labeled)
    print('Flare peaks count:', len(flare_peaks))
    if len(flare_peaks) == 0:
        print('No flare peaks found; nothing to label.')
        return
    windows = make_windows(labeled, window_s=10*60, step_s=60)
    print('Total windows:', len(windows))
    windows = label_windows(windows, flare_peaks, horizon_s=30*60)
    counts = windows['label'].value_counts(dropna=False)
    print('Window label distribution:')
    print(counts.to_string())


if __name__ == '__main__':
    main()
