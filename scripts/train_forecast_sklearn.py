#!/usr/bin/env python3
"""Train a RandomForest with class_weight='balanced' using the existing window/label pipeline."""
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import joblib

ROOT = Path(__file__).resolve().parents[1]
LABELED = ROOT / 'Solar Low Energy X-ray Spectrometer' / 'output' / 'labeled_solexs.csv'
COMBINED_CAT = ROOT / 'output' / 'solexs_hel1os_combined_catalog.csv'
OUT_DIR = ROOT / 'output'
OUT_DIR.mkdir(parents=True, exist_ok=True)


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


def main(args):
    labeled = load_data()
    flare_peaks = get_flare_peaks(labeled)
    if len(flare_peaks) == 0:
        print('No flare peaks found; exiting')
        return
    print('Found', len(flare_peaks), 'flare peaks')
    windows = make_windows(labeled, window_s=args.window_min * 60, step_s=args.step_s)
    print('Created', len(windows), 'windows')
    windows = label_windows(windows, flare_peaks, horizon_s=args.horizon_min * 60)
    print('Positive windows:', int(windows['label'].sum()), 'Negative windows:', int((windows['label'] == 0).sum()))

    X = windows[['mean', 'std', 'max', 'last', 'slope']]
    y = windows['label']

    # TIME-BASED SPLIT (no temporal leakage): train on earlier 80% of time, test on final 20%
    time_split = windows['end'].quantile(0.80)
    train_mask = windows['end'] <= time_split
    test_mask = ~train_mask
    
    X_train = X[train_mask].reset_index(drop=True)
    X_test = X[test_mask].reset_index(drop=True)
    y_train = y[train_mask].reset_index(drop=True)
    y_test = y[test_mask].reset_index(drop=True)
    win_train = windows[train_mask].reset_index(drop=True)
    win_test = windows[test_mask].reset_index(drop=True)
    
    print(f'TIME-BASED SPLIT (leakage-free):')
    print(f'  Train: {train_mask.sum()} windows, Test: {test_mask.sum()} windows')
    print(f'  Train positive: {y_train.sum()} ({100*y_train.sum()/len(y_train):.2f}%), negative: {(y_train==0).sum()}')
    print(f'  Test positive: {y_test.sum()} ({100*y_test.sum()/len(y_test):.2f}%), negative: {(y_test==0).sum()}')
    print(f'  Train ends before {time_split}, test begins after')

    clf = RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_test, y_proba)
    except Exception:
        auc = float('nan')

    print('\nRESULTS (time-based holdout):')
    print(f'  Accuracy: {acc:.3f}')
    print(f'  Precision: {prec:.3f}')
    print(f'  Recall: {rec:.3f}')
    print(f'  F1: {f1:.3f}')
    print(f'  ROC-AUC: {auc:.3f}')

    tp_mask = (y_test == 1) & (y_pred == 1)
    if tp_mask.any():
        lead_times = win_test.loc[tp_mask, 'lead_s']
        avg_lead = np.nanmean(lead_times) / 60.0
    else:
        avg_lead = float('nan')
    print(f'  Average lead time (minutes) for true positives: {avg_lead:.2f}')

    joblib.dump(clf, OUT_DIR / 'forecast_model_rf.joblib')
    print('\nSaved model to', OUT_DIR / 'forecast_model_rf.joblib')

    results = win_test.copy()
    results['y_true'] = y_test
    results['y_pred'] = y_pred
    results['y_proba'] = y_proba
    results.to_csv(OUT_DIR / 'forecast_results_rf.csv', index=False)
    print('Saved results to', OUT_DIR / 'forecast_results_rf.csv')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--window-min', type=int, default=10)
    parser.add_argument('--horizon-min', type=int, default=30)
    parser.add_argument('--step-s', type=int, default=60)
    args = parser.parse_args()
    main(args)
