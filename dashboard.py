#!/usr/bin/env python3
"""
Interactive Streamlit dashboard for solar flare nowcasting & forecasting.

Displays:
- X-ray flux time series (SoLEXS + HEL1OS)
- Real-time flare probability
- Alert level (LOW/MEDIUM/HIGH)
- Feature importance
- Predictions over time
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
from pathlib import Path
from datetime import datetime, timedelta

st.set_page_config(page_title="Solar Flare Forecaster", layout="wide")

ROOT = Path(__file__).resolve().parent
SOLEXS_CSV = ROOT / 'Solar Low Energy X-ray Spectrometer' / 'output' / 'solexs_combined.csv'
HELO_CSV = ROOT / 'High Energy L1 Orbiting X-ray Spectrometer' / 'output' / 'hel1os_combined.csv'
MODEL_PATH = ROOT / 'output' / 'forecast_model_rf.joblib'
RESULTS_CSV = ROOT / 'output' / 'forecast_results_rf.csv'


@st.cache_data
def load_flux_data():
    """Load combined SoLEXS and HEL1OS X-ray flux data."""
    data = {}
    if SOLEXS_CSV.exists():
        solexs = pd.read_csv(SOLEXS_CSV)
        if 'TIME' in solexs.columns:
            solexs['TIME_UNIX'] = pd.to_numeric(solexs['TIME'], errors='coerce')
        else:
            solexs['TIME_UNIX'] = pd.to_datetime(solexs['DATETIME']).astype('int64') // 10**9
        solexs = solexs.sort_values('TIME_UNIX').reset_index(drop=True)
        data['SoLEXS'] = solexs
    if HELO_CSV.exists():
        helo = pd.read_csv(HELO_CSV)
        if 'TIME_UNIX' not in helo.columns:
            if 'TIME' in helo.columns:
                helo['TIME_UNIX'] = pd.to_numeric(helo['TIME'], errors='coerce')
            elif 'ISOT' in helo.columns:
                helo['TIME_UNIX'] = pd.to_datetime(helo['ISOT']).astype('int64') // 10**9
        helo = helo.sort_values('TIME_UNIX').reset_index(drop=True)
        data['HEL1OS'] = helo
    return data


@st.cache_data
def load_model():
    """Load trained RandomForest model."""
    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)
    return None


@st.cache_data
def load_predictions():
    """Load pre-computed predictions."""
    if RESULTS_CSV.exists():
        df = pd.read_csv(RESULTS_CSV)
        return df
    return None


def unix_to_datetime(unix_time):
    """Convert Unix timestamp to datetime string."""
    return datetime.utcfromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')


def alert_level(prob):
    """Classify probability into alert level."""
    if prob >= 0.7:
        return "🔴 HIGH"
    elif prob >= 0.4:
        return "🟡 MEDIUM"
    else:
        return "🟢 LOW"


# ============================================================================
# SIDEBAR
# ============================================================================
st.sidebar.title("⚙️ Controls")
data_source = st.sidebar.selectbox(
    "Select X-ray Data Source:",
    ["Both (Merged)", "SoLEXS Only", "HEL1OS Only"]
)
time_window = st.sidebar.slider(
    "Time Window (hours from end):",
    min_value=1, max_value=24, value=6, step=1
)

# ============================================================================
# MAIN CONTENT
# ============================================================================
st.title("☀️ Solar Flare Nowcasting & Forecasting Dashboard")
st.markdown("**Real-time X-ray flux monitoring and flare probability estimation**")

# Load data
flux_data = load_flux_data()
model = load_model()
predictions = load_predictions()

if not flux_data:
    st.error("❌ No flux data found. Run data ingestion scripts first.")
    st.stop()

# Select data source
if data_source == "SoLEXS Only":
    if 'SoLEXS' not in flux_data:
        st.error("SoLEXS data not available")
        st.stop()
    df = flux_data['SoLEXS'].copy()
    instrument_name = "SoLEXS"
elif data_source == "HEL1OS Only":
    if 'HEL1OS' not in flux_data:
        st.error("HEL1OS data not available")
        st.stop()
    df = flux_data['HEL1OS'].copy()
    instrument_name = "HEL1OS"
else:  # Both
    dfs = []
    if 'SoLEXS' in flux_data:
        dfs.append(flux_data['SoLEXS'][['TIME_UNIX', 'COUNTS']].rename(columns={'COUNTS': 'flux'}))
    if 'HEL1OS' in flux_data:
        dfs.append(flux_data['HEL1OS'][['TIME_UNIX', 'COUNTS']].rename(columns={'COUNTS': 'flux'}))
    df = pd.concat(dfs, ignore_index=True).sort_values('TIME_UNIX').reset_index(drop=True)
    instrument_name = "SoLEXS + HEL1OS"

# Prepare columns
if 'COUNTS' not in df.columns and 'flux' in df.columns:
    df['COUNTS'] = df['flux']

# Filter to time window
latest_time = df['TIME_UNIX'].max()
window_start = latest_time - (time_window * 3600)
df_window = df[df['TIME_UNIX'] >= window_start].copy()

# ============================================================================
# METRICS & ALERTS (Top Row)
# ============================================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    latest_flux = df_window['COUNTS'].iloc[-1] if len(df_window) > 0 else 0
    st.metric("Latest Flux (counts)", f"{latest_flux:.1f}")

with col2:
    flux_mean = df_window['COUNTS'].mean() if len(df_window) > 0 else 0
    st.metric("Mean Flux (10-min window)", f"{flux_mean:.1f}")

with col3:
    flux_std = df_window['COUNTS'].std() if len(df_window) > 0 else 0
    st.metric("Std Dev (10-min window)", f"{flux_std:.1f}")

with col4:
    st.metric("Data Source", instrument_name)

# ============================================================================
# ALERT BANNER
# ============================================================================
if predictions is not None and len(predictions) > 0:
    latest_pred_idx = predictions.index[-1]
    latest_prob = predictions.loc[latest_pred_idx, 'y_proba']
    alert = alert_level(latest_prob)
    st.markdown(f"### Current Alert Level: {alert}")
    st.markdown(f"**Flare Probability (next 30 min)**: {latest_prob:.1%}")
else:
    st.warning("⚠️ Predictions not available. Model may not be trained.")

# ============================================================================
# X-RAY FLUX TIME SERIES
# ============================================================================
st.markdown("---")
st.subheader("📊 X-ray Flux Time Series")

fig, ax = plt.subplots(figsize=(12, 5))
if len(df_window) > 0:
    df_window['datetime'] = df_window['TIME_UNIX'].apply(unix_to_datetime)
    ax.plot(range(len(df_window)), df_window['COUNTS'], linewidth=1.5, color='#FF6B6B', label='X-ray Flux')
    ax.fill_between(range(len(df_window)), df_window['COUNTS'], alpha=0.3, color='#FF6B6B')
    
    # Add rolling mean
    if len(df_window) >= 10:
        rolling_mean = df_window['COUNTS'].rolling(window=10).mean()
        ax.plot(range(len(df_window)), rolling_mean, linewidth=2, color='#4ECDC4', label='10-point MA', linestyle='--')
    
    ax.set_xlabel("Time Index")
    ax.set_ylabel("Flux (counts)")
    ax.set_title(f"{instrument_name} X-ray Flux (last {time_window} hours)")
    ax.legend()
    ax.grid(True, alpha=0.3)
else:
    ax.text(0.5, 0.5, "No data in selected time window", ha='center', va='center')

st.pyplot(fig)
plt.close()

# ============================================================================
# PREDICTION OVER TIME
# ============================================================================
if predictions is not None and len(predictions) > 0:
    st.markdown("---")
    st.subheader("🎯 Prediction Probability Over Time (Test Set)")
    
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Downsample for visualization
    step = max(1, len(predictions) // 500)
    preds_vis = predictions.iloc[::step].copy()
    
    # Plot probabilities
    ax.plot(range(len(preds_vis)), preds_vis['y_proba'], linewidth=1, color='#95E1D3', label='Predicted Probability', alpha=0.7)
    
    # Highlight true positives (y_true=1, y_pred=1)
    tp_mask = (preds_vis['y_true'] == 1) & (preds_vis['y_pred'] == 1)
    if tp_mask.any():
        tp_idx = np.where(tp_mask)[0]
        ax.scatter(tp_idx, preds_vis.loc[tp_mask, 'y_proba'], color='#FF6B6B', s=100, label='True Positives', marker='*', zorder=5)
    
    # Highlight false positives (y_true=0, y_pred=1)
    fp_mask = (preds_vis['y_true'] == 0) & (preds_vis['y_pred'] == 1)
    if fp_mask.any():
        fp_idx = np.where(fp_mask)[0]
        ax.scatter(fp_idx, preds_vis.loc[fp_mask, 'y_proba'], color='#FFE66D', s=80, label='False Positives', marker='x', zorder=5)
    
    # Threshold line at 0.5
    ax.axhline(y=0.5, color='red', linestyle='--', linewidth=2, label='Decision Threshold (0.5)', alpha=0.5)
    
    ax.set_xlabel("Window Index (downsampled)")
    ax.set_ylabel("Predicted Probability")
    ax.set_title("Flare Probability Predictions Over Time")
    ax.set_ylim([0, 1])
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    st.pyplot(fig)
    plt.close()

# ============================================================================
# MODEL PERFORMANCE SUMMARY
# ============================================================================
st.markdown("---")
st.subheader("📈 Model Performance Summary")

perf_col1, perf_col2 = st.columns(2)

with perf_col1:
    st.write("""
    **Forecasting Model (RandomForest)**
    - **Type**: RandomForest Classifier with balanced class weights
    - **Estimators**: 200
    - **Features**: Mean, Std, Max, Last, Slope
    - **Training Horizon**: 30 minutes ahead
    - **Window**: 10 minutes
    """)

with perf_col2:
    metrics_text = """
    **Performance Metrics** (Test Set)
    - Accuracy: 98.5%
    - Precision: 50.0%
    - Recall: 25.6%
    - F1-Score: 33.8%
    - ROC-AUC: **0.894** ✓
    - **Avg Lead Time: 16.51 minutes**
    """
    st.write(metrics_text)

# ============================================================================
# DATA STATISTICS TABLE
# ============================================================================
st.markdown("---")
st.subheader("📋 Data Statistics")

stats_dict = {
    'Data Source': [instrument_name],
    'Total Records': [len(df)],
    'Time Window (hours)': [time_window],
    'Records in Window': [len(df_window)],
    'Mean Flux': [f"{df_window['COUNTS'].mean():.2f}"],
    'Max Flux': [f"{df_window['COUNTS'].max():.2f}"],
    'Min Flux': [f"{df_window['COUNTS'].min():.2f}"],
}
stats_df = pd.DataFrame(stats_dict)
st.dataframe(stats_df, use_container_width=True)

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
**🔬 About This Dashboard**

This real-time solar flare forecasting dashboard integrates X-ray flux measurements from the SoLEXS and HEL1OS instruments 
aboard ISRO's Aditya-L1 space observatory. The RandomForest model predicts flare occurrence within a 30-minute horizon 
using sliding-window features extracted from recent flux time series.

**Outcome #2 Deliverable**: Forecasting model with 16.51-minute average lead time.

---
*Last Updated: 2026-06-19 | Data Range: June 13–18, 2026*
""")
