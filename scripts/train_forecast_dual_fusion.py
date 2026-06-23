#!/usr/bin/env python3
"""Train a dual-instrument (SoLEXS + HEL1OS) solar flare forecasting model.

This script implements a major research gap: raw time-series data fusion between
soft X-rays (SoLEXS) and hard X-rays (HEL1OS) at the second level, and extracts
the Spectral Hardness Ratio (HEL1OS/SoLEXS) as a precursor feature.
"""
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import joblib

ROOT = Path(__file__).resolve().parents[1]
SOLEXS_CSV = ROOT / 'Solar Low Energy X-ray Spectrometer' / 'output' / 'solexs_combined.csv'
HELO_CSV = ROOT / 'High Energy L1 Orbiting X-ray Spectrometer' / 'output' / 'hel1os_combined.csv'
MATCHED = ROOT / 'Solar Low Energy X-ray Spectrometer' / 'output' / 'matched_flares.csv'
OUT_DIR = ROOT / 'output'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_and_merge_data():
    print("Loading SoLEXS combined data...")
    solexs = pd.read_csv(SOLEXS_CSV)
    solexs['TIME'] = pd.to_numeric(solexs['TIME'], errors='coerce').round().astype(int)
    solexs = solexs.drop_duplicates(subset=['TIME']).sort_values('TIME').reset_index(drop=True)

    print("Loading HEL1OS combined data...")
    helo = pd.read_csv(HELO_CSV)
    helo['TIME'] = pd.to_numeric(helo['TIME'], errors='coerce').round().astype(int)
    helo = helo.drop_duplicates(subset=['TIME']).sort_values('TIME').reset_index(drop=True)

    print("Merging on Unix Time...")
    merged = pd.merge(solexs, helo, on='TIME', suffixes=('_SOLEXS', '_HEL1OS'))
    merged = merged.rename(columns={'COUNTS_SOLEXS': 'COUNTS_S', 'COUNTS_HEL1OS': 'COUNTS_H'})
    print(f"Merged time series: {len(merged):,} rows")
    return merged


def get_flare_peaks():
    matched = pd.read_csv(MATCHED)
    peaks_unix = pd.to_datetime(matched['PEAK_DT']).map(lambda x: int(x.timestamp())).values
    return peaks_unix


def make_windows_fusion(df, window_s=600, step_s=60):
    times = df['TIME'].values
    counts_s = df['COUNTS_S'].values
    counts_h = df['COUNTS_H'].values
    
    # Compute baseline rolling stats on the fly
    # We use past-only to avoid lookahead contamination
    df['ROLL_MED_S'] = df['COUNTS_S'].shift(1).rolling(window=window_s, min_periods=60).median()
    df['ROLL_STD_S'] = df['COUNTS_S'].shift(1).rolling(window=window_s, min_periods=60).std()
    
    df['ROLL_MED_H'] = df['COUNTS_H'].shift(1).rolling(window=window_s, min_periods=60).median()
    df['ROLL_STD_H'] = df['COUNTS_H'].shift(1).rolling(window=window_s, min_periods=60).std()
    
    # Fill baseline stats
    df = df.dropna(subset=['ROLL_MED_S', 'ROLL_STD_S', 'ROLL_MED_H', 'ROLL_STD_H']).reset_index(drop=True)
    
    times = df['TIME'].values
    counts_s = df['COUNTS_S'].values
    counts_h = df['COUNTS_H'].values
    
    # Z-scores & Hardness ratio
    z_s = (df['COUNTS_S'] - df['ROLL_MED_S']) / (df['ROLL_STD_S'] + 1e-5)
    z_h = (df['COUNTS_H'] - df['ROLL_MED_H']) / (df['ROLL_STD_H'] + 1e-5)
    ratio = counts_h / (counts_s + 1e-5)
    
    z_s_vals = z_s.values
    z_h_vals = z_h.values
    ratio_vals = ratio
    
    end_time = times[-1]
    start_time = times[0]
    
    windows = []
    # Fast window extraction via searchsorted
    for window_start in np.arange(start_time, end_time - window_s + 1, step_s):
        window_end = window_start + window_s
        idx_start = np.searchsorted(times, window_start, side='left')
        idx_end = np.searchsorted(times, window_end, side='left')
        if idx_start == idx_end:
            continue
            
        w_t = times[idx_start:idx_end]
        w_cs = counts_s[idx_start:idx_end]
        w_ch = counts_h[idx_start:idx_end]
        w_zs = z_s_vals[idx_start:idx_end]
        w_zh = z_h_vals[idx_start:idx_end]
        w_rat = ratio_vals[idx_start:idx_end]
        
        # SoLEXS features
        mean_s = np.mean(w_cs)
        std_s = np.std(w_cs)
        max_s = np.max(w_cs)
        last_s = w_cs[-1]
        
        # HEL1OS features
        mean_h = np.mean(w_ch)
        std_h = np.std(w_ch)
        max_h = np.max(w_ch)
        last_h = w_ch[-1]
        
        # Fusion Z-scores & Spectral Hardness Ratio
        z_mean_s = np.mean(w_zs)
        z_max_s = np.max(w_zs)
        z_mean_h = np.mean(w_zh)
        z_max_h = np.max(w_zh)
        
        mean_ratio = np.mean(w_rat)
        max_ratio = np.max(w_rat)
        last_ratio = w_rat[-1]
        
        # Slopes
        if len(w_t) > 1:
            coeffs_s = np.polyfit(w_t - w_t[0], w_cs, 1)
            slope_s = coeffs_s[0]
            coeffs_h = np.polyfit(w_t - w_t[0], w_ch, 1)
            slope_h = coeffs_h[0]
        else:
            slope_s = 0.0
            slope_h = 0.0
            
        windows.append({
            'end': window_end,
            # SoLEXS
            'mean_s': mean_s, 'std_s': std_s, 'max_s': max_s, 'last_s': last_s, 'slope_s': slope_s,
            # HEL1OS
            'mean_h': mean_h, 'std_h': std_h, 'max_h': max_h, 'last_h': last_h, 'slope_h': slope_h,
            # Fusion
            'z_mean_s': z_mean_s, 'z_max_s': z_max_s,
            'z_mean_h': z_mean_h, 'z_max_h': z_max_h,
            'mean_ratio': mean_ratio, 'max_ratio': max_ratio, 'last_ratio': last_ratio
        })
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
    df = load_and_merge_data()
    flare_peaks = get_flare_peaks()
    
    print("Creating sliding windows with dual-instrument features...")
    windows = make_windows_fusion(df, window_s=args.window_min * 60, step_s=args.step_s)
    print(f"Created {len(windows):,} windows")
    
    windows = label_windows(windows, flare_peaks, horizon_s=args.horizon_min * 60)
    print(f"Positive windows: {int(windows['label'].sum())}, Negative: {int((windows['label'] == 0).sum())}")
    
    feature_cols = [
        'mean_s', 'std_s', 'max_s', 'last_s', 'slope_s',
        'mean_h', 'std_h', 'max_h', 'last_h', 'slope_h',
        'z_mean_s', 'z_max_s', 'z_mean_h', 'z_max_h',
        'mean_ratio', 'max_ratio', 'last_ratio'
    ]
    
    X = windows[feature_cols]
    y = windows['label']
    
    # TIME-BASED SPLIT (leakage-free holdout)
    time_split = windows['end'].quantile(0.80)
    train_mask = windows['end'] <= time_split
    test_mask = ~train_mask
    
    X_train = X[train_mask]
    y_train = y[train_mask]
    X_test = X[test_mask]
    y_test = y[test_mask]
    
    print(f"\nTraining Dual-Fusion model (leakage-free)...")
    print(f"  Train samples: {len(X_train)} (pos={y_train.sum()})")
    print(f"  Test samples: {len(X_test)} (pos={y_test.sum()})")
    
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
        
    tp_mask = (y_test == 1) & (y_pred == 1)
    if tp_mask.any():
        lead_times = windows.loc[test_mask].loc[tp_mask, 'lead_s']
        avg_lead = np.nanmean(lead_times) / 60.0
    else:
        avg_lead = float('nan')
        
    print("\nRESULTS (Dual-Fusion Model, time-based split):")
    print(f"  Accuracy: {acc:.3f}")
    print(f"  Precision: {prec:.3f}")
    print(f"  Recall: {rec:.3f}")
    print(f"  F1: {f1:.3f}")
    print(f"  ROC-AUC: {auc:.3f}")
    print(f"  Average lead time: {avg_lead:.2f} minutes")
    
    # Save model and predictions
    joblib.dump(clf, OUT_DIR / 'forecast_model_rf_fusion.joblib')
    print(f"\nSaved model to {OUT_DIR / 'forecast_model_rf_fusion.joblib'}")
    
    results = windows[test_mask].copy()
    results['y_true'] = y_test
    results['y_pred'] = y_pred
    results['y_proba'] = y_proba
    results.to_csv(OUT_DIR / 'forecast_results_rf_fusion.csv', index=False)
    print(f"Saved predictions to {OUT_DIR / 'forecast_results_rf_fusion.csv'}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--window-min', type=int, default=10)
    parser.add_argument('--horizon-min', type=int, default=30)
    parser.add_argument('--step-s', type=int, default=60)
    args = parser.parse_args()
    main(args)
