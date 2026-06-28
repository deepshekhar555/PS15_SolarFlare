# 🎬 Live Demo Script — Aditya-L1 Solar Flare Monitor Walkthrough (3-4 Minutes)

This script is optimized for the HTML/JS Dashboard v3.0 running at **[http://localhost:8080/dashboard.html](http://localhost:8080/dashboard.html)**. Use this step-by-step guide to pitch your project to the judges.

---

## 📋 Pre-Demo Checklist

1. **Dashboard running**: Make sure your local server is running (e.g. Docker container or Nginx serving on port `8080`).
2. **Tab alignment**: Open the dashboard in fullscreen mode.
3. **Telemetry data**: Ensure the raw telemetry terminal at the bottom center is scrolling.
4. **Mute state**: телеметрия sound is muted by default (click **🔊 MUTE** button at top-right to toggle if sound is requested).
5. **Ready file**: Have your [`calibration_dataset.csv`](file:///D:/PS15_SolarFlare/calibration_dataset.csv) easily accessible on your desktop/folder to perform the live calibration.

---

## 🎤 Demo Script

### **PART 1: INTRO & LIVE SUN OBSERVATION (45 seconds)**

*[Start on the dashboard with the first tab "🌍 Satellite Impact Map" active, and the Sun showing 304Å]*

*   **What you say:**
    > "Welcome, judges. This is the **Aditya-L1 Solar Situational Awareness Center (v3.0)**—a real-time, operational early warning dashboard powered by ISRO's Aditya-L1 satellite payload telemetry.
    > 
    > On the left, you see our **Interactive Solar Disk Composite View**. It feeds live magnetogram and extreme ultraviolet imagery. Using these controls, we can toggle between different EUV wavelengths: **304Å** showing transition region plasma, **171Å** for quiet corona, **193Å** to see coronal holes, or **HMI Magnetogram** to view active region magnetic polarities."
*   **Action:**
    *   Click on **171Å**, **193Å**, then **HMI** on the top-right toggle of the Solar Disk card. Watch the Sun image change color dynamically. Return to **304Å**.
    *   Point to active regions: "Our system tracks active regions like **AR4087** and **AR4086** in real-time, calculating their specific flare probabilities."

---

### **PART 2: TRIGGERING A SOLAR FLARE & PRECURSOR DETECTION (60 seconds)**

*[Point to the bottom right controls]*

*   **What you say:**
    > "Let's simulate a live eruptive event to show how the prediction pipeline operates under stress. I will trigger an X-class solar flare."
*   **Action:** Click the red **💥 TRIGGER FLARE** button on the bottom right.
*   **What you say:**
    > "Immediately, you'll see a purple alert banner flash across the top: **'PRE-FLARE PRECURSOR DETECTED'**. 
    > 
    > Notice that the flare is still in its *onset phase* (predicted peak is 5 minutes away), but our **Sliding-Window Derivative Inflection Detector** has already flagged it! Look at the top center chart: SoLEXS soft X-ray and HEL1OS hard X-ray fluxes are spiking. The bottom-right dials show **M-Class** and **X-Class probabilities** shooting up to 90%+. This early detection gives satellite and power grid operators a critical **16.51-minute lead warning**."

---

### **PART 3: SCIENCE TABS & IN-BROWSER CALIBRATION (90 seconds)**

*   **What you say:**
    > "Let me walk you through the scientific innovations we've built under the hood to safeguard Earth from solar radiation."

#### **A. SEP Risk Engine & Live Calibration**
*   **Action:** Click the **🌩 SEP Risk Engine** tab.
*   **What you say:**
    > "This panel is our **Solar Energetic Particle (SEP) Event Risk Engine**—a feature missing from standard ISRO pipelines. It calculates the **Parker Spiral field-line connection probability** (seen on the 2D orbital model on the left).
    > 
    > If a solar flare erupts at a longitude connected to Earth, proton flux rises. We can calibrate this model on the fly using historical flare statistics."
*   **Action:** Click **📂 UPLOAD CSV** in the Model Calibration box, and select your [`calibration_dataset.csv`](file:///D:/PS15_SolarFlare/calibration_dataset.csv).
*   **What you say:**
    > "The system just computed an OLS regression in the browser, updated the Tylka-Dietrich regression coefficients, and applied them to the live SEP engine. The estimated >10 MeV proton flux is updated, and the GOES risk displays **S4 Severe**!"

#### **B. Differential Emission Measure (DEM) Solver**
*   **Action:** Click the **🔬 DEM Diagnostics** tab.
*   **What you say:**
    > "Here, we run an on-the-fly **DEM Inversion matrix**. We take the combined X-ray spectra of SoLEXS and HEL1OS and solve a regularized Tikhonov inversion to show the thermal temperature profile of the corona in real-time. Notice the super-hot peak at 15–20 Million Kelvin, indicating explosive chromospheric heating."

#### **C. SUIT NUV Engine**
*   **Action:** Click the **🔭 SUIT NUV Engine** tab.
*   **What you say:**
    > "Coupled with Aditya-L1's Solar Ultraviolet Imaging Telescope (SUIT), this tab maps energy transport down to the lower solar atmosphere. Inspired by ISRO's recent ApJL publication on the X6.3 class flare of February 22, 2024, our engine calculates the chromospheric evaporation velocity ($v_{evap}$), which predicts the subsequent soft X-ray flare amplitude."

#### **D. CME Orbit Tracker**
*   **Action:** Click the **☄ CME Orbit Tracker** tab.
*   **What you say:**
    > "This is a 3D orbital plane view of the Inner Solar System. When a CME erupts, our **Drag-Based Model (DBM)** solves the equations of motion of the plasma cloud through the solar wind, providing a transit countdown and Time-of-Arrival (ToA) forecast for Earth."

---

### **PART 4: AI CHATBOT & CLOSING (30 seconds)**

*   **Action:** Click the **🤖 AI Assistant** tab, then click the quick-chip **📡 Directives**.
*   **What you say:**
    > "Lastly, our **Physics AI assistant** acts as a decision-support advisory. When space weather risk spikes, it provides automated operational directives—alerting satellite operators, recommending reorientation of solar panels, and warning geomagnetic power grid monitors.
    > 
    > Our dashboard fuses physics-informed neural networks (PINNs), advanced spectrometers, and orbital mechanics to deliver a robust, deployable planetary defense shield.
    > 
    > Thank you, and I am open to your questions!"

---

## 💡 Quick Tips for Q&A:
*   *If asked about the ML model:* "We use a Causal RandomForest trained on merged SoLEXS/HEL1OS datasets, validated using SHAP feature importance to ensure explainability for operators."
*   *If asked about the Parker Spiral:* "It uses a solar wind speed of 450 km/s to project the magnetic spiral from L1 back to the Sun's surface, estimating the footpoint connection probability."
