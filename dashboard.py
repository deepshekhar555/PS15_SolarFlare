#!/usr/bin/env python3
"""
Solar Flare Nowcasting & Forecasting Dashboard with AI Assistant.
Integrates live telemetry, RandomForest models, and a Gemini-powered conversational AI.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
import os
from pathlib import Path
from datetime import datetime
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# ============================================================================
# PAGE & THEME CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Solar Flare Forecaster",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS styling (zinc-dark theme)
CSS = """
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
    /* Hide default Streamlit chrome */
    header[data-testid="stHeader"], footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {
        display: none !important;
    }
    
    /* Global Background and Typography */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container {
        background-color: #09090b !important;
        color: #fafafa !important;
        font-family: 'Outfit', -apple-system, sans-serif !important;
    }
    
    .block-container {
        padding: 1.5rem 2rem 2rem !important;
        max-width: 1400px !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0c0c0f !important;
        border-right: 1px solid #1e1e24 !important;
    }
    
    /* Custom Card Design */
    .custom-card {
        background-color: #0c0c0f;
        border: 1px solid #1e1e24;
        border-radius: 10px;
        padding: 1.25rem 1.4rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    /* KPI Metrics Card */
    .kpi-card {
        background-color: #0c0c0f;
        border: 1px solid #1e1e24;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        text-align: left;
    }
    .kpi-label {
        font-size: 0.8rem;
        color: #a1a1aa;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #fafafa;
        margin-top: 0.2rem;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Custom Alert Banners */
    .alert-banner {
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 1.25rem;
        border: 1px solid transparent;
        display: flex;
        flex-direction: column;
    }
    .alert-low {
        background-color: rgba(16, 185, 129, 0.08);
        border-color: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }
    .alert-medium {
        background-color: rgba(245, 158, 11, 0.08);
        border-color: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
    }
    .alert-high {
        background-color: rgba(239, 68, 68, 0.08);
        border-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    .alert-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    .alert-desc {
        font-size: 0.9rem;
        color: #a1a1aa;
    }

    /* HTML Data Table */
    .data-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    .data-table th {
        text-align: left;
        padding: 0.75rem 1rem;
        color: #a1a1aa;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-bottom: 1px solid #1e1e24;
        background-color: #0c0c0f;
    }
    .data-table td {
        padding: 0.75rem 1rem;
        color: #fafafa;
        border-bottom: 1px solid #16161a;
    }
    .data-table tr:last-child td {
        border-bottom: none;
    }
    .data-table tr:hover td {
        background-color: #131316;
    }

    /* Tabs Styling */
    div[data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: #0c0c0f !important;
        border: 1px solid #1e1e24 !important;
        border-radius: 8px !important;
        padding: 4px !important;
        margin-bottom: 1.5rem !important;
    }
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #a1a1aa !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        padding: 0.5rem 1.25rem !important;
        border: 1px solid transparent !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #fafafa !important;
        background-color: #1e1e24 !important;
        border-color: #27272a !important;
    }
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {
        display: none !important;
    }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ============================================================================
# DATA & MODEL LOADERS
# ============================================================================
ROOT = Path(__file__).resolve().parent
SOLEXS_CSV = ROOT / 'Solar Low Energy X-ray Spectrometer' / 'output' / 'solexs_combined.csv'
HELO_CSV = ROOT / 'High Energy L1 Orbiting X-ray Spectrometer' / 'output' / 'hel1os_combined.csv'

MODEL_PATH_SINGLE = ROOT / 'output' / 'forecast_model_rf.joblib'
RESULTS_CSV_SINGLE = ROOT / 'output' / 'forecast_results_rf.csv'
MODEL_PATH_FUSION = ROOT / 'output' / 'forecast_model_rf_fusion.joblib'
RESULTS_CSV_FUSION = ROOT / 'output' / 'forecast_results_rf_fusion.csv'


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
def load_model(is_fusion=False):
    """Load trained RandomForest model."""
    path = MODEL_PATH_FUSION if is_fusion else MODEL_PATH_SINGLE
    if path.exists():
        return joblib.load(path)
    return None


@st.cache_data
def load_predictions(is_fusion=False):
    """Load pre-computed predictions."""
    path = RESULTS_CSV_FUSION if is_fusion else RESULTS_CSV_SINGLE
    if path.exists():
        return pd.read_csv(path)
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
# SIDEBAR CONTROLS
# ============================================================================
st.sidebar.markdown("### ☀️ SolarSentinels Panel")
st.sidebar.markdown("---")

data_source = st.sidebar.selectbox(
    "Select X-ray Data Source:",
    ["Both (Merged)", "SoLEXS Only", "HEL1OS Only"]
)

time_window = st.sidebar.slider(
    "Time Window (hours from end):",
    min_value=1, max_value=24, value=6, step=1
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 AI Assistant Config")
# Sidebar API Key input for Gemini Chatbot
gemini_key = st.sidebar.text_input(
    "Enter Gemini API Key (optional):",
    type="password",
    value=os.environ.get("GEMINI_API_KEY", ""),
    help="Provide your Gemini API key to activate the live conversational chatbot in the AI Assistant tab."
)

st.sidebar.markdown("---")
st.sidebar.info("🔬 Operational telemetry is sourced from Aditya-L1 instruments (June 13–18, 2026).")

# ============================================================================
# DATA PREPARATION
# ============================================================================
flux_data = load_flux_data()
is_fusion = (data_source == "Both (Merged)")
model = load_model(is_fusion=is_fusion)
predictions = load_predictions(is_fusion=is_fusion)

if data_source == "HEL1OS Only":
    st.sidebar.warning("⚠️ HEL1OS-only model is not trained separately. Showing predictions from SoLEXS-trained model as a fallback.")

if not flux_data:
    st.error("❌ No flux data found. Please run the ingestion scripts first.")
    st.stop()

# Select active data source
if data_source == "SoLEXS Only":
    if 'SoLEXS' not in flux_data:
        st.error("SoLEXS data not available.")
        st.stop()
    df = flux_data['SoLEXS'].copy()
    instrument_name = "SoLEXS"
elif data_source == "HEL1OS Only":
    if 'HEL1OS' not in flux_data:
        st.error("HEL1OS data not available.")
        st.stop()
    df = flux_data['HEL1OS'].copy()
    instrument_name = "HEL1OS"
else:  # Merged/Both
    dfs = []
    if 'SoLEXS' in flux_data:
        dfs.append(flux_data['SoLEXS'][['TIME_UNIX', 'COUNTS']].rename(columns={'COUNTS': 'flux'}))
    if 'HEL1OS' in flux_data:
        dfs.append(flux_data['HEL1OS'][['TIME_UNIX', 'COUNTS']].rename(columns={'COUNTS': 'flux'}))
    df = pd.concat(dfs, ignore_index=True).sort_values('TIME_UNIX').reset_index(drop=True)
    instrument_name = "SoLEXS + HEL1OS"

if 'COUNTS' not in df.columns and 'flux' in df.columns:
    df['COUNTS'] = df['flux']

# Filter telemetry to active time window
latest_time = df['TIME_UNIX'].max()
window_start = latest_time - (time_window * 3600)
df_window = df[df['TIME_UNIX'] >= window_start].copy()

# Compute live metrics
latest_flux = df_window['COUNTS'].iloc[-1] if len(df_window) > 0 else 0
flux_mean = df_window['COUNTS'].mean() if len(df_window) > 0 else 0
flux_std = df_window['COUNTS'].std() if len(df_window) > 0 else 0

# Retrieve latest predictions
if predictions is not None and len(predictions) > 0:
    latest_pred_idx = predictions.index[-1]
    latest_prob = predictions.loc[latest_pred_idx, 'y_proba']
    alert = alert_level(latest_prob)
else:
    latest_prob = 0.0
    alert = "🟢 LOW"

# ============================================================================
# MAIN LAYOUT
# ============================================================================
st.title("☀️ Aditya-L1 Solar Flare Forecasting System")
st.markdown("Automated space weather nowcasting and machine-learning risk assessment.")

# Navigation Tabs
tab_telemetry, tab_ai, tab_model = st.tabs([
    "📊 Real-Time Telemetry & Forecasts",
    "🤖 AI Space Weather Assistant",
    "📈 Validation & Model Info"
])

# ----------------------------------------------------------------------------
# TAB 1: REAL-TIME TELEMETRY & FORECASTS
# ----------------------------------------------------------------------------
with tab_telemetry:
    # 1. Alert Banner
    if alert == "🔴 HIGH":
        alert_class = "alert-high"
        alert_desc = "Impulsive flare phase signature detected. High probability of non-thermal acceleration. Satellite operators should initiate protection protocols."
    elif alert == "🟡 MEDIUM":
        alert_class = "alert-medium"
        alert_desc = "Precursor thermal activity detected (slow rise phase). Coronal plasma heating underway. Monitor channels closely."
    else:
        alert_class = "alert-low"
        alert_desc = "Stable coronal conditions. No significant pre-heating or impulsive flux signatures observed."

    st.markdown(f"""
    <div class="alert-banner {alert_class}">
        <div class="alert-title">Current Alert Level: {alert} (Probability: {latest_prob:.1%})</div>
        <div class="alert-desc">{alert_desc}</div>
    </div>
    """, unsafe_allow_html=True)

    # 2. KPI Cards Row
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Latest Flux (counts)</div>
            <div class="kpi-value">{latest_flux:.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Mean Flux (window)</div>
            <div class="kpi-value">{flux_mean:.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Std Dev (window)</div>
            <div class="kpi-value">{flux_std:.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Data Source</div>
            <div class="kpi-value" style="font-size: 1.35rem; font-weight: 600; padding-top: 0.4rem;">{instrument_name}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Telemetry Plots
    plot_col1, plot_col2 = st.columns([2, 1])
    
    with plot_col1:
        st.markdown("### 📊 X-ray Flux Time Series")
        fig, ax = plt.subplots(figsize=(10, 4.2))
        
        # Set dark theme styles for the chart
        fig.patch.set_facecolor('#0c0c0f')
        ax.set_facecolor('#0c0c0f')
        ax.spines['bottom'].set_color('#27272a')
        ax.spines['top'].set_color('#27272a')
        ax.spines['left'].set_color('#27272a')
        ax.spines['right'].set_color('#27272a')
        ax.xaxis.label.set_color('#a1a1aa')
        ax.yaxis.label.set_color('#a1a1aa')
        ax.tick_params(colors='#71717a', which='both')
        
        if len(df_window) > 0:
            df_window['datetime'] = df_window['TIME_UNIX'].apply(unix_to_datetime)
            ax.plot(range(len(df_window)), df_window['COUNTS'], linewidth=1.5, color='#ef4444', label='X-ray Flux')
            ax.fill_between(range(len(df_window)), df_window['COUNTS'], alpha=0.12, color='#ef4444')
            
            # Add moving average
            if len(df_window) >= 10:
                rolling_mean = df_window['COUNTS'].rolling(window=10).mean()
                ax.plot(range(len(df_window)), rolling_mean, linewidth=1.5, color='#10b981', label='10-point MA', linestyle='--')
            
            ax.set_xlabel("Telemetry Samples (Window: {} hours)".format(time_window))
            ax.set_ylabel("Counts")
            ax.legend(facecolor='#0c0c0f', edgecolor='#27272a', labelcolor='#fafafa')
            ax.grid(True, alpha=0.08, color='#fafafa')
        else:
            ax.text(0.5, 0.5, "No telemetry data in selected window.", ha='center', va='center', color='#71717a')
            
        st.pyplot(fig)
        plt.close()

    with plot_col2:
        st.markdown("### 🎯 Forecasting Trend (Test Set)")
        fig, ax = plt.subplots(figsize=(5, 4.2))
        
        fig.patch.set_facecolor('#0c0c0f')
        ax.set_facecolor('#0c0c0f')
        ax.spines['bottom'].set_color('#27272a')
        ax.spines['top'].set_color('#27272a')
        ax.spines['left'].set_color('#27272a')
        ax.spines['right'].set_color('#27272a')
        ax.xaxis.label.set_color('#a1a1aa')
        ax.yaxis.label.set_color('#a1a1aa')
        ax.tick_params(colors='#71717a', which='both')
        
        if predictions is not None and len(predictions) > 0:
            # Downsample for visualization
            step = max(1, len(predictions) // 150)
            preds_vis = predictions.iloc[::step].copy()
            
            ax.plot(range(len(preds_vis)), preds_vis['y_proba'], linewidth=1.2, color='#60a5fa', label='Prob', alpha=0.7)
            
            tp_mask = (preds_vis['y_true'] == 1) & (preds_vis['y_pred'] == 1)
            if tp_mask.any():
                tp_idx = np.where(tp_mask)[0]
                ax.scatter(tp_idx, preds_vis.loc[tp_mask, 'y_proba'], color='#ef4444', s=60, label='True Pos', marker='*', zorder=5)
                
            fp_mask = (preds_vis['y_true'] == 0) & (preds_vis['y_pred'] == 1)
            if fp_mask.any():
                fp_idx = np.where(fp_mask)[0]
                ax.scatter(fp_idx, preds_vis.loc[fp_mask, 'y_proba'], color='#f59e0b', s=45, label='False Pos', marker='x', zorder=5)
            
            ax.axhline(y=0.5, color='#ef4444', linestyle=':', linewidth=1.5, label='Threshold (0.5)', alpha=0.6)
            ax.set_xlabel("Evaluation Windows")
            ax.set_ylabel("Probability")
            ax.set_ylim([-0.05, 1.05])
            ax.legend(facecolor='#0c0c0f', edgecolor='#27272a', labelcolor='#fafafa', fontsize=8)
            ax.grid(True, alpha=0.08, color='#fafafa')
        else:
            ax.text(0.5, 0.5, "Predictions not loaded.", ha='center', va='center', color='#71717a')
            
        st.pyplot(fig)
        plt.close()

    # 4. Data Statistics Table
    st.markdown("### 📋 Live Data Statistics")
    stats_html = f"""
    <table class="data-table">
        <thead>
            <tr>
                <th>Telemetry Source</th>
                <th>Total Records</th>
                <th>Selected Window (hours)</th>
                <th>Samples in Window</th>
                <th>Mean Flux</th>
                <th>Maximum Flux</th>
                <th>Minimum Flux</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>{instrument_name}</td>
                <td>{len(df):,}</td>
                <td>{time_window}</td>
                <td>{len(df_window):,}</td>
                <td>{df_window['COUNTS'].mean():.2f}</td>
                <td>{df_window['COUNTS'].max():.2f}</td>
                <td>{df_window['COUNTS'].min():.2f}</td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(stats_html, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# TAB 2: AI SPACE WEATHER ASSISTANT
# ----------------------------------------------------------------------------
with tab_ai:
    st.markdown("### 🤖 SolarSentinels AI Space Weather Assistant")
    st.markdown("A physics-informed AI companion to help operators interpret telemetry, explain anomalies, and guide solar flare mitigation.")

    # Initialize chat history in Streamlit session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Check if a Gemini API Key is available
    if gemini_key:
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=gemini_key)
            
            # Setup Gemini model
            ai_model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=(
                    "You are the SolarSentinels AI Assistant, an expert solar physicist and space weather forecaster. "
                    "Your purpose is to help mission operators understand real-time solar activity, interpret the Aditya-L1 dashboard data, "
                    "and explain the physics of solar flares. Be concise, scientific, highly accurate, and helpful. "
                    "When discussing the active telemetry, refer to the numbers injected in the system context."
                )
            )
            
            # Display past messages
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Chat input field
            if user_prompt := st.chat_input("Ask a question about the active telemetry or solar flare physics..."):
                # Render user message
                with st.chat_message("user"):
                    st.markdown(user_prompt)
                st.session_state.chat_history.append({"role": "user", "content": user_prompt})

                # Construct rich real-time context to feed to Gemini
                telemetry_context = f"""
[REAL-TIME CONTEXT - DO NOT EXPOSE DIRECTLY AS SYSTEM CODE, USE AS CONTEXT TO ANSWER USER]
- Telemetry Source: {instrument_name}
- Latest Flux: {latest_flux:.1f} counts
- 10-Min Mean Flux: {flux_mean:.1f} counts
- 10-Min Rolling Std Dev: {flux_std:.1f} counts
- ML Flare Probability (next 30 min): {latest_prob:.1%}
- Current Alert Level: {alert}
- Total Merged Nowcast Events in Catalog: 108 events
- Nowcaster Recall: 93.2% when benchmarked against NOAA GOES catalog
- Model Performance Lead Time: 16.51 minutes (stratified random split) / 4.57 minutes (leakage-free chronological split)
- Dataset Range: June 13–18, 2026

User Query: {user_prompt}
"""

                # Stream Gemini response
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    full_ai_response = ""
                    
                    # Start chat and generate streaming content
                    chat_session = ai_model.start_chat(history=[])
                    stream = chat_session.send_message(telemetry_context, stream=True)
                    
                    for chunk in stream:
                        full_ai_response += chunk.text
                        response_placeholder.markdown(full_ai_response + "▌")
                    response_placeholder.markdown(full_ai_response)
                
                st.session_state.chat_history.append({"role": "assistant", "content": full_ai_response})

        except Exception as e:
            st.error(f"Failed to initialize Gemini AI: {str(e)}")
            st.warning("Please verify that your Gemini API Key is valid and that you have internet connectivity.")
            
    else:
        # Fallback: Rule-Based Expert AI Analyst
        st.markdown(f"""
        <div class="alert-banner alert-medium" style="margin-bottom: 1.5rem;">
            <div class="alert-title">🔑 Gemini Conversational Assistant Offline</div>
            <div class="alert-desc">Enter your Gemini API Key in the sidebar to activate the live multi-turn chat assistant. In the meantime, our local <b>Physics-Informed Expert System</b> has compiled a real-time report based on the active telemetry below.</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🔬 Local AI Physics Analyst Report")
        st.markdown("This automated report evaluates current data parameters against solar plasma models:")
        
        report = []
        
        # 1. State-based evaluation
        if latest_prob >= 0.7:
            report.append(f"""
#### 🔴 Alert Status: IMPULSIVE FLARE PHASE RISK
* **Risk Probability**: {latest_prob:.1%}
* **Physics Signature**: The telemetry indicates a high-probability trigger. In solar physics, this corresponds to the rapid conversion of stored magnetic energy into kinetic and thermal energy. 
* **Thermal-Nonthermal Transition**: If SoLEXS (SXR) and HEL1OS (HXR) counts are spiking concurrently, it indicates that high-energy, accelerated electrons (non-thermal) are colliding with the dense lower corona/chromosphere (Neupert Effect). This process heats the surrounding plasma, causing a massive surge in soft X-rays.
* **Operational Directive**: Reorient spacecraft solar sensors, safe sensitive microelectronics, and prepare for potential high-frequency radio absorption (communications blackout).
""")
        elif latest_prob >= 0.4:
            report.append(f"""
#### 🟡 Alert Status: PRE-FLARE THERMAL PLASMA HEATING
* **Risk Probability**: {latest_prob:.1%}
* **Physics Signature**: A positive slope in soft X-ray flux indicates the *pre-flare slow rise phase*. This is caused by gradual magnetic heating of plasma loops in the active region before the primary magnetic reconnection trigger.
* **Operational Directive**: Maintain active monitoring. Ensure secondary communication networks are standing by.
""")
        else:
            report.append(f"""
#### 🟢 Alert Status: NOMINAL / CORONAL BACKGROUND
* **Risk Probability**: {latest_prob:.1%}
* **Physics Signature**: X-ray flux is stable and matches background coronal emissions. No pre-heating signatures, rapid rises, or anomalous standard deviation slopes are present.
* **Operational Directive**: Standard operational configurations. Nominal status.
""")

        # 2. Oscillatory / QPP signatures
        if flux_std >= 40:
            report.append(f"""
#### 🌊 Signature Detected: QUASI-PERIODIC PULSATIONS (QPPs)
* **Observation**: Rolling standard deviation is elevated ({flux_std:.1f} counts).
* **Physics Signature**: High-frequency fluctuations in X-ray flux indicate the presence of Quasi-Periodic Pulsations (QPPs). These pulsations are physical manifestations of magnetohydrodynamic (MHD) waves (such as kink or sausage modes) oscillating within active region magnetic loops, or periodic bursts of magnetic reconnection. QPPs are highly correlated in space weather literature with imminent energetic solar flare eruptions.
""")
            
        # 3. Instrument fusion signatures
        if is_fusion:
            report.append("""
#### 🔗 Instrument Integration: SOLEXS + HEL1OS DUAL FUSION
* **Physics Feature**: The forecasting model is actively incorporating cross-instrument features, notably the **Spectral Hardness Ratio** ($COUNTS_{HEL1OS} / COUNTS_{SoLEXS}$). Fusing soft X-rays (thermal, plasma-dominated) and hard X-rays (non-thermal, particle-acceleration-dominated) directly resolves spatial and spectral ambiguities, allowing the RandomForest model to discriminate true flare signatures with higher physical fidelity.
""")

        st.markdown("\n\n".join(report))

# ----------------------------------------------------------------------------
# TAB 3: VALIDATION & MODEL INFO
# ----------------------------------------------------------------------------
with tab_model:
    st.markdown("### 📈 Machine Learning Validation & Performance")
    st.markdown("We evaluate our forecasting model using two validation regimes to ensure complete scientific transparency and avoid lookahead contamination.")

    perf_col1, perf_col2 = st.columns(2)

    with perf_col1:
        if is_fusion:
            st.markdown("""
            ### 🤖 Model Architecture: Dual-Instrument Fusion
            * **Algorithm**: RandomForest Classifier with balanced class weights
            * **Estimators**: 200 trees
            * **Input Window**: 10 minutes (60-second steps)
            * **Forecasting Horizon**: 30 minutes ahead (binary classification)
            * **Feature Vector (17 features)**:
              - **SoLEXS**: Mean, Std Dev, Max, Last Count, Slope
              - **HEL1OS**: Mean, Std Dev, Max, Last Count, Slope
              - **Fused Statistics**: Cross-instrument Z-scores, Mean/Max/Last **Spectral Hardness Ratio** ($COUNTS_{HEL1OS} / COUNTS_{SoLEXS}$)
            * **Class Imbalance Strategy**: Resampling weights inversely proportional to class frequencies to force the forest to learn rare precursor patterns ( flares represent only ~1.5% of total windows).
            """)
        else:
            st.markdown("""
            ### 🤖 Model Architecture: Single Instrument (SoLEXS)
            * **Algorithm**: RandomForest Classifier with balanced class weights
            * **Estimators**: 200 trees
            * **Input Window**: 10 minutes (60-second steps)
            * **Forecasting Horizon**: 30 minutes ahead (binary classification)
            * **Feature Vector (5 features)**:
              - **SoLEXS**: Mean, Std Dev, Max, Last Count, Slope
            * **Class Imbalance Strategy**: Resampling weights inversely proportional to class frequencies to prevent the model from converging to a trivial 'always negative' predictor.
            """)

    with perf_col2:
        if predictions is not None and len(predictions) > 0 and 'y_true' in predictions.columns:
            y_true = predictions['y_true']
            y_pred = predictions['y_pred']
            y_proba = predictions['y_proba']
            
            acc = accuracy_score(y_true, y_pred)
            prec = precision_score(y_true, y_pred, zero_division=0)
            rec = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)
            
            try:
                auc = roc_auc_score(y_true, y_proba)
            except Exception:
                auc = 0.5
                
            # Average Lead Time
            tp_mask = (y_true == 1) & (y_pred == 1)
            if tp_mask.any() and 'lead_s' in predictions.columns:
                avg_lead = np.nanmean(predictions.loc[tp_mask, 'lead_s']) / 60.0
            else:
                avg_lead = float('nan')
                
            lead_time_str = f"{avg_lead:.2f} minutes" if not np.isnan(avg_lead) else "N/A (No True Positives)"
            
            st.markdown(f"""
            ### 📊 Dynamic Validation Metrics (Test Set)
            * **Accuracy**: **{acc:.1%}**
            * **Precision**: **{prec:.1%}** (1 in {1/prec:.1f} predictions is a true flare)
            * **Recall**: **{rec:.1%}** (catches {rec:.1%} of actual flares)
            * **F1-Score**: **{f1:.3f}**
            * **ROC-AUC**: **{auc:.3f}**
            * **Average Lead Time**: **{lead_time_str}**
            """)
            
            if is_fusion:
                st.info("💡 Note: Fusing SoLEXS and HEL1OS data tracks the physical heating-to-particle-acceleration phase transition, reducing false alarm uncertainty.")
            else:
                st.info("💡 Note: Model trained on soft X-ray (SoLEXS) counts alone.")
        else:
            st.warning("⚠️ Prediction metrics could not be computed. Please train the corresponding model.")

    st.markdown("---")
    st.markdown("### 🔬 Leakage-Free Chronological Split vs. Leaky Random Split")
    
    split_col1, split_col2 = st.columns(2)
    with split_col1:
        st.markdown("""
        #### 1. Stratified Random Split (Leaky)
        * **ROC-AUC**: **0.894**
        * **Avg Lead Time**: **16.51 minutes**
        * **Evaluation**: Commonly used in literature but flawed. Since sliding windows overlap (e.g., window at $t$ and $t+60s$ share 90% of their data), random splitting puts highly correlated windows into both the training and test sets. This creates **temporal leakage**, leading to artificially inflated performance metrics.
        """)
    with split_col2:
        st.markdown("""
        #### 2. Chronological Split (Leakage-Free)
        * **ROC-AUC**: **~0.533**
        * **Avg Lead Time**: **~4.57 minutes**
        * **Evaluation**: The scientifically honest baseline. We train the model on the first 80% of the timeline and test on the final 20%. This strictly respects time, preventing future data from contaminating past predictions. The near-random ROC-AUC is expected due to having only **16 training events** in our 6-day window, defining a clear data-volume roadmap for Phase 2.
        """)

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #71717a; font-size: 0.8rem; margin-top: 1rem;">
    SolarSentinels Solar Flare Forecasting Pipeline | Aditya-L1 Hackathon 2026
    <br>
    <i>Team: Deep Shekhar, Rituraj Saha, Mahalaxmi, Ashfaque | Adamas University, Kolkata</i>
</div>
""", unsafe_allow_html=True)
