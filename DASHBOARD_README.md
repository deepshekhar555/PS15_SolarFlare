# Aditya-L1 Solar Situational Awareness Dashboard v3.0 — Quick Start Guide

This guide describes how to run and present the **Premium HTML/JS/CSS Dashboard v3.0** for the Aditya-L1 Solar Flare Monitoring System.

---

## 🚀 How to Run the Dashboard

You can launch the dashboard using either of the two methods below:

### Method 1: Local Docker Container (Recommended ✓)
The project includes a lightweight Docker configuration using `nginx:alpine` to host the static assets:
```bash
# 1. Build the dashboard container
docker build -t solarflare-dashboard -f Dockerfile.dashboard .

# 2. Run the container on port 8080
docker run -d -p 8080:80 --name solarflare-dashboard-live solarflare-dashboard
```
Open **[http://localhost:8080/dashboard.html](http://localhost:8080/dashboard.html)** in your default browser.

### Method 2: Direct Local Browser Execution
Because the dashboard is fully client-side (built on pure HTML5, vanilla CSS, and vanilla JS), you can open it directly without any installation:
* Double-click on [`dashboard.html`](file:///D:/PS15_SolarFlare/dashboard.html) in your file explorer.
* Or open it directly using your browser's File Open dialog.

---

## 🌟 Dashboard Features

### 1. ☀ Solar Disk Composite View (Left Panel)
*   **Wavelength Toggle**: Switch between **304Å**, **171Å**, **193Å**, and **HMI Magnetogram** to view different layers of the solar atmosphere in real-time.
*   **Active Regions**: Automatically highlights regions of interest (**AR4087**, **AR4086**, **AR4085**).

### 2. 📊 Real-Time Telemetry & Forecasts (Center Panel)
*   **Telemetry Chart**: Fuses live **SoLEXS (Soft X-rays)** and **HEL1OS (Hard X-rays)** counts in real-time with a 1-second cadence.
*   **Probability Chart**: Predicts class-wise flare probability (B, C, M, X class) for the next 3 hours.
*   **Raw Telemetry Feed**: Real-time terminal showing live serial data packet transmissions from the L1 Lagrange point.

### 3. 🔬 Interactive Scientific Tabs (Bottom Section)
*   **🌍 Satellite Impact Map**: Plots real-time D-region ionospheric absorption blackouts and orbit tracks over a world map.
*   **🧠 AI Explainability**: Shows live **SHAP feature importance bars** and calculations for the **Neupert Coherence Index** (verifying the Neupert effect).
*   **🔬 DEM Diagnostics**: Solves a **regularized Tikhonov inversion** in real-time on every tick to plot the temperature distribution of the corona (1 MK to 40 MK).
*   **🌩 SEP Risk Engine**: Uses the **Tylka-Dietrich empirical model** and a **2D Parker Spiral model** to calculate if high-energy protons have a magnetic connection to Earth.
*   **🔭 SUIT NUV Engine**: Couples X-rays with near-UV observations to model chromospheric evaporation velocity ($v_{evap}$) and ribbons.
*   **🤖 AI Assistant**: A physics-trained advisory assistant with pre-programmed quick chips (Directives, Hardness Ratio, QPP Physics).

---

## ⚙ In-Browser Model Calibration

Under the **🌩 SEP Risk Engine** tab, you can perform live OLS calibration:
1. Click **📂 UPLOAD CSV** under the *Model Calibration* box.
2. Select [`calibration_dataset.csv`](file:///D:/PS15_SolarFlare/calibration_dataset.csv).
3. The dashboard will instantly run OLS regression to fit the Tylka-Dietrich parameters ($a, b, c$) in your browser, update the estimated proton flux, and save the calibrated model to `localStorage`!
