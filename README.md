# Solar Flare Nowcasting & Forecasting System using Aditya-L1 X-ray Data

An end-to-end, real-time space weather monitoring and forecasting pipeline utilizing raw X-ray flux data from ISRO's **Aditya-L1** space observatory. The system integrates causal multi-instrument data fusion, real-time nowcasting, machine-learning-based forecasting, and an interactive Streamlit dashboard for mission operators.

Developed by team **SolarSentinels** (Adamas University, Kolkata) for the ISRO Aditya-L1 Hackathon.

---

## 🌌 Project Overview & Motivation

Space weather events—particularly solar flares—pose significant risks to modern infrastructure, including satellite electronics, high-frequency communications, and terrestrial power grids. Traditional forecasting workflows rely heavily on manual, post-facto expert analysis, resulting in latency gaps of 15 to 30 minutes. 

Our system addresses this operational challenge by providing an automated, low-latency pipeline that:
1. **Harmonizes and fuses** raw soft X-ray (SXR) counts from the **SoLEXS** instrument and hard X-ray (HXR) counts from the **HEL1OS** instrument.
2. **Nowcasts** active flares in real time with a causal, rolling-baseline detector.
3. **Forecasts** solar flare occurrence up to 30 minutes in advance using a physics-informed RandomForest architecture.
4. **Visualizes** live telemetry, alert levels (🟢 LOW, 🟡 MEDIUM, 🔴 HIGH), and probabilistic risk indices on a unified control dashboard.

---

## 🛠️ Key Scientific & Technical Innovations

### 1. Causal Rolling-Baseline Nowcasting
Typical automated event detection in literature employs centered smoothing windows (such as Gaussian or Savitzky-Golay filters) that incorporate future data points ($t + \Delta t$), making them impossible to deploy in real-time telemetry feeds. We implement a **strictly causal rolling baseline** (shifting past-only windows) to guarantee real-time compatibility. The nowcaster achieves a **93.2% recall** (68 out of 73 flares recovered) when benchmarked against the official NOAA GOES-16/18 solar flare event list.

### 2. Raw Multi-Instrument Data Fusion
We align the raw, high-cadence time-series from SoLEXS (1-second cadence) and HEL1OS (cadence-aware time-binning) during their overlapping observation windows, matching over 259,000 shared timestamps. This allows us to compute the **Spectral Hardness Ratio** ($COUNTS_{HEL1OS} / COUNTS_{SoLEXS}$) in real time. 

### 3. Physics-Informed Feature Engineering
Our machine learning model leverages features directly representing solar flare physics:
* **Pre-Flare Slow Rise**: Rolling means and positive slopes over 10-minute windows capture the gradual heating of coronal plasma before the main impulsive phase.
* **Quasi-Periodic Pulsations (QPPs)**: Rolling standard deviations capture high-frequency oscillatory variance caused by MHD waves and magnetic reconnection in coronal loops.
* **Neupert Effect Modeling**: The Spectral Hardness Ratio and cross-instrument Z-scores track the rapid physical transition from thermal plasma heating to non-thermal particle acceleration.

### 4. Leakage-Free Validation Rigor
To ensure academic and operational credibility, we evaluate our forecasting model using two distinct validation splits:
* **Informal Random Stratified Split**: Yields an optimistic **ROC-AUC of 0.894** and an average lead time of **16.51 minutes**. This represents a baseline when overlapping sliding windows are permitted across train/test splits (temporal leakage).
* **Leakage-Free Chronological Split (Train 80% / Test 20%)**: Prevents temporal leakage by dividing the data at a strict historical boundary. On our exploratory 6-day dataset (16 confirmed flares, 14,139 windows), this yields an honest baseline **ROC-AUC of ~0.533** and an average lead time of **~4.57 minutes**. These honest numbers serve as our scientific baseline, proving the viability of the architecture while establishing a clear data-volume roadmap.

---

## 📊 Performance Summary

| Metric | Value | Evaluation Context |
|---|---|---|
| **Nowcasting Recall (NOAA GOES)** | **93.2%** | 68 / 73 GOES-listed flares recovered (only 5 weak C-class missed) |
| **Nowcasting Precision** | **35.8%** | 76 / 212 merged events match GOES; remaining 136 represent real sub-threshold microflares |
| **Forecasting ROC-AUC (Random Split)** | **0.894** | Inflated by temporal leakage (used for literature comparison) |
| **Forecasting ROC-AUC (Chronological)** | **~0.533** | Strict, leakage-free holdout (Phase-1 honest baseline) |
| **Average Lead Time (Random Split)** | **16.51 min** | Average warning time before flare peak |
| **Average Lead Time (Chronological)** | **~4.57 min** | Average warning time under strict chronological evaluation |
| **Inference Latency** | **< 1 ms** | Per window on commodity hardware (highly scalable) |

---

## 📂 Repository Structure

```
PS15_SolarFlare/
├── Solar Low Energy X-ray Spectrometer/     # SoLEXS-specific pipeline files
│   ├── data/                                # Raw SoLEXS zip files (ignored in Git)
│   ├── output/                              # Processed SoLEXS time series & nowcast catalogs
│   └── scripts/                             # Ingestion, nowcasting, and validation scripts
├── High Energy L1 Orbiting X-ray Spectrometer/ # HEL1OS-specific pipeline files
│   ├── data/                                # Raw HEL1OS fits files (ignored in Git)
│   ├── output/                              # Processed HEL1OS time series & nowcast catalogs
│   └── scripts/                             # Ingestion, nowcasting, and tuning scripts
├── scripts/                                 # Shared forecasting and evaluation scripts
│   ├── train_forecast_sklearn.py            # Trains single-instrument RandomForest
│   ├── train_forecast_dual_fusion.py        # Trains dual-instrument fusion model
│   ├── merge_catalogs.py                    # Integrates SoLEXS & HEL1OS nowcast catalogs
│   └── [helper scripts]                     # Statistical checks, false alarm analysis, etc.
├── output/                                  # Shared outputs, trained models, and results
│   ├── forecast_model_rf.joblib             # Trained single-instrument model
│   ├── forecast_model_rf_fusion.joblib      # Trained dual-instrument fusion model
│   ├── forecast_results_rf.csv              # Predictions & probabilities (single)
│   └── forecast_results_rf_fusion.csv       # Predictions & probabilities (fusion)
├── dashboard.py                             # Interactive Streamlit operator dashboard
├── run_full_pipeline.ps1                    # PowerShell wrapper to execute full pipeline
├── requirements.txt                         # Python package dependencies
└── README.md                                # This documentation
```

---

## 🚀 Getting Started

### Prerequisites
* Python 3.9+
* PowerShell (for running the pipeline wrapper) or Git Bash

### 1. Installation
Clone the repository and set up a virtual environment:
```bash
# Clone the repository
git clone https://github.com/deepshekhar555/PS15_SolarFlare.git
cd PS15_SolarFlare

# Create and activate a virtual environment
python -m venv .venv
# On Windows PowerShell:
& .\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Ingestion & Training Pipeline
To run the full pipeline (combining raw FITS/Zip files, running nowcasting, labeling flares, and training both the single-instrument and dual-instrument forecasting models):
```powershell
& .\run_full_pipeline.ps1
```
*Note: Raw data files are expected to be in the respective instrument `data/` subdirectories. If you have PRADAN download URLs, place them in `pradan_urls.txt` and export your `PRADAN_COOKIE` before running.*

### 3. Launch the Operator Dashboard
Start the interactive dashboard to visualize the telemetry and model predictions:
```bash
streamlit run dashboard.py
```
The dashboard will automatically open in your browser (defaulting to `http://localhost:8501`).

---

## 📈 Future Roadmap: Phase 2 and Beyond

Our Phase-1 prototype demonstrates a complete, working end-to-end pipeline. To scale this into an operational-grade space weather asset, our Phase-2 development roadmap focuses on:
1. **Data Expansion**: Ingesting the full multi-month Aditya-L1 archive from the PRADAN portal to scale up the training set to 100+ confirmed flares, stabilizing the RandomForest and enabling deeper sequence models (e.g., LSTMs or Transformers).
2. **Spacecraft Attitude Correction**: Ingesting spacecraft roll, pitch, and yaw telemetry to normalize counts against collimator area variations during off-pointing maneuvers.
3. **Physical Unit Calibration**: Implementing on-the-fly spectral deconvolution using Detector Response Matrices (DRMs) to convert raw counts into physical flux units ($W/m^2$ or $photons/cm^2/s/keV$).
4. **Multimodal Spatial Fusion**: Integrating spatial imaging from Aditya-L1's **SUIT** (Solar Ultraviolet Imaging Telescope) to resolve spatial active region ambiguity.

---

## 👥 Team & Contact

* **Team Name**: SolarSentinels
* **Institutional Affiliation**: Adamas University, Kolkata
* **Primary Investigator & Tech Lead**: Deep Shekhar (`deepshekhar555`)
* **Data & Validation**: Mahalaxmi & Ashfaque

For inquiries, please contact: `[Your Contact Email]`
