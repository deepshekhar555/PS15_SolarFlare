#!/usr/bin/env python3
"""Train a baseline forecasting model using SoLEXS data.

Pipeline:
- Load `Solar Low Energy X-ray Spectrometer/output/solexs_combined.csv` and `.../labeled_solexs.csv`.
- Create sliding windows of length `WINDOW_MIN` (default 10 minutes) with step `STEP_S`.
- Label a window positive if a flare peak occurs in the next `HORIZON_MIN` minutes after the window end.
- Features: mean, std, max, slope (linear fit), last value.
- Train RandomForestClassifier baseline.
- Evaluate accuracy, precision, recall, ROC-AUC, and average lead time for true positives.
- Save model to `output/forecast_model.joblib` and predictions to `output/forecast_results.csv`.
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import pickle
import warnings

warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parents[1]
SOLEXS_COMBINED = ROOT / 'Solar Low Energy X-ray Spectrometer' / 'output' / 'solexs_combined.csv'
LABELED = ROOT / 'Solar Low Energy X-ray Spectrometer' / 'output' / 'labeled_solexs.csv'
COMBINED_CAT = ROOT / 'output' / 'solexs_hel1os_combined_catalog.csv'
OUT_DIR = ROOT / 'output'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    # labeled_solexs should contain DATETIME or TIME and IS_FLARE flags
    labeled = pd.read_csv(LABELED)
    # Prefer numeric TIME if present
    if 'TIME' in labeled.columns:
        labeled['TIME_UNIX'] = pd.to_numeric(labeled['TIME'], errors='coerce')
        # if TIME is unix float, ok; otherwise try DATETIME
        if labeled['TIME_UNIX'].isna().all() and 'DATETIME' in labeled.columns:
            labeled['TIME_UNIX'] = pd.to_datetime(labeled['DATETIME']).astype('int64') // 10**9
    else:
        labeled['TIME_UNIX'] = pd.to_datetime(labeled['DATETIME']).astype('int64') // 10**9

    labeled = labeled.sort_values('TIME_UNIX').reset_index(drop=True)
    return labeled


def make_windows(df, window_s=600, step_s=60):
    times = df['TIME_UNIX'].values
    counts = df['COUNTS'].values
    end_time = times[-1]
    start_time = times[0]
    windows = []
    idx = 0
    # build index -> time mapping
    for window_start in np.arange(start_time, end_time - window_s + 1, step_s):
        window_end = window_start + window_s
        # select indices within [window_start, window_end)
        mask = (times >= window_start) & (times < window_end)
        if not np.any(mask):
            continue
        vals = counts[mask]
        t_vals = times[mask]
        # features
        mean = np.mean(vals)
        std = np.std(vals)
        mx = np.max(vals)
        last = vals[-1]
        # slope via simple linear regression
        if len(t_vals) > 1:
            coeffs = np.polyfit(t_vals - t_vals[0], vals, 1)
            slope = coeffs[0]
        else:
            slope = 0.0
        windows.append({
            'start': window_start,
            'end': window_end,
            'mean': mean,
            'std': std,
            'max': mx,
            'last': last,
            'slope': slope
        })
    return pd.DataFrame(windows)


def label_windows(windows, flare_peaks_unix, horizon_s=600, min_lead_s=0):
    # For each window, label 1 if any flare peak in (end, end+horizon]
    labels = []
    lead_times = []
    for _, row in windows.iterrows():
        end = row['end']
        window_peaks = flare_peaks_unix[(flare_peaks_unix > end) & (flare_peaks_unix <= end + horizon_s)]
        if len(window_peaks) > 0:
            labels.append(1)
            # lead time = time from window end to earliest peak
            lead_times.append(window_peaks.min() - end)
        else:
            labels.append(0)
            lead_times.append(np.nan)
    windows['label'] = labels
    windows['lead_s'] = lead_times
    return windows


def main(args):
    labeled = load_data()
    # flare peaks: find rows flagged as IS_FLARE and maybe PEAK_TIME from matched_flares
    # Here use combined catalog peak times too
    flare_peaks = []
    # Prefer combined catalog if available
    if COMBINED_CAT.exists():
        cc = pd.read_csv(COMBINED_CAT)
        if 'PEAK_TIME' in cc.columns:
            try:
                # if PEAK_TIME is ISO string
                if cc['PEAK_TIME'].dtype == object:
                    peaks_unix = pd.to_datetime(cc['PEAK_TIME']).astype('int64') // 10**9
                else:
                    peaks_unix = pd.to_numeric(cc['PEAK_TIME'], errors='coerce')
                flare_peaks = peaks_unix.dropna().astype(int).values
            except Exception:
                flare_peaks = []
    if len(flare_peaks) == 0:
        # fallback to labeled_solexs where IS_FLARE marks flare rows; use PEAK times from that labeling if present
        if 'IS_FLARE' in labeled.columns:
            # compute peaks by grouping contiguous IS_FLARE rows and taking max COUNTS
            flares = []
            mask = labeled['IS_FLARE'] == 1
            labeled['grp'] = (mask != mask.shift(1)).cumsum()
            groups = labeled[mask].groupby('grp')
            for _, g in groups:
                # pick time of max COUNTS
                idx = g['COUNTS'].idxmax()
                flare_time = g.loc[idx, 'TIME_UNIX']
                flares.append(flare_time)
            flare_peaks = np.array(flares, dtype=int)

    if len(flare_peaks) == 0:
        print('No flare peaks found in combined catalog or labeled data. Exiting.')
        return

    print(f'Found {len(flare_peaks)} flare peaks for labeling')

    # Create windows over labeled timeline (use labeled which has full cadence)
    window_s = args.window_min * 60
    step_s = args.step_s
    windows = make_windows(labeled, window_s=window_s, step_s=step_s)

    print(f'Created {len(windows)} windows (window={args.window_min}min, step={step_s}s)')

    # Label windows for horizon
    horizon_s = args.horizon_min * 60
    windows = label_windows(windows, flare_peaks, horizon_s=horizon_s)

    # Drop windows without enough data? Keep all
    X = windows[['mean', 'std', 'max', 'last', 'slope']]
    y = windows['label']

    # Simple train/test split
    X_np = X.values
    y_np = y.values
    rng = np.random.RandomState(42)
    perm = rng.permutation(len(X_np))
    X_sh = X_np[perm]
    y_sh = y_np[perm]
    split = int(0.8 * len(X_sh))
    X_train = X_sh[:split]
    y_train = y_sh[:split]
    X_test = X_sh[split:]
    y_test = y_sh[split:]
    win_test = windows.iloc[perm[split:]].reset_index(drop=True)

    print('Training logistic regression (numpy gradient descent)...')
    X_train_aug = np.hstack([np.ones((X_train.shape[0], 1)), X_train])
    X_test_aug = np.hstack([np.ones((X_test.shape[0], 1)), X_test])
    w = np.zeros(X_train_aug.shape[1])
    lr = 0.01
    for epoch in range(1000):
        z = X_train_aug.dot(w)
        pred = 1.0 / (1.0 + np.exp(-z))
        grad = X_train_aug.T.dot(pred - y_train) / len(y_train)
        w -= lr * grad

    def predict_proba(Xa):
        z = Xa.dot(w)
        return 1.0 / (1.0 + np.exp(-z))

    y_proba = predict_proba(X_test_aug)
    y_pred = (y_proba >= 0.5).astype(int)

    def safe_div(a, b):
        return a / b if b != 0 else 0.0

    acc = float((y_pred == y_test).mean())
    prec = safe_div(((y_pred == 1) & (y_test == 1)).sum(), (y_pred == 1).sum())
    rec = safe_div(((y_pred == 1) & (y_test == 1)).sum(), (y_test == 1).sum())
    try:
        order = np.argsort(y_proba)
        tpr = np.cumsum(y_test[order] == 1) / max(1, (y_test == 1).sum())
        fpr = np.cumsum(y_test[order] == 0) / max(1, (y_test == 0).sum())
        auc = np.trapz(tpr, fpr)
    except Exception:
        auc = float('nan')

    print('Results:')
    print(f'  Accuracy: {acc:.3f}')
    print(f'  Precision: {prec:.3f}')
    print(f'  Recall: {rec:.3f}')
    print(f'  ROC-AUC: {auc:.3f}')

    tp_mask = (y_test == 1) & (y_pred == 1)
    if tp_mask.any():
        lead_times = win_test.loc[tp_mask, 'lead_s']
        avg_lead = np.nanmean(lead_times) / 60.0
    else:
        avg_lead = float('nan')

    print(f'Average lead time (minutes) for true positives: {avg_lead:.2f}')

    # Save model and results
    with open(OUT_DIR / 'forecast_model.pkl', 'wb') as f:
        pickle.dump({'weights': w, 'features': ['bias','mean','std','max','last','slope']}, f)
    print('Saved model to', OUT_DIR / 'forecast_model.pkl')

    results = win_test.copy()
    results['y_true'] = y_test
    results['y_pred'] = y_pred
    results['y_proba'] = y_proba
    results.to_csv(OUT_DIR / 'forecast_results.csv', index=False)
    print('Saved forecast results to', OUT_DIR / 'forecast_results.csv')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--window-min', type=int, default=10, help='Window length in minutes')
    parser.add_argument('--horizon-min', type=int, default=30, help='Prediction horizon in minutes')
    parser.add_argument('--step-s', type=int, default=60, help='Window step in seconds')
    args = parser.parse_args()
    main(args)
