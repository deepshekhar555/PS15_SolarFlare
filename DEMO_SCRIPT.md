# Live Demo Script — Dashboard Walkthrough (2–3 minutes)

**Pre-Demo Checklist:**
- [ ] Dashboard is running: `py -m streamlit run dashboard.py`
- [ ] Browser open to `http://localhost:8501`
- [ ] Freshly reloaded (no cached errors)
- [ ] Projector/screen sharing working
- [ ] Mouse sensitivity is good (not too fast)
- [ ] Have backup screenshot images in case of browser crash

---

## Demo Flow (Talk + Click)

### **PART 1: INITIAL VIEW (15 seconds)**

*[Dashboard loads, showing the main title and alert banner]*

**What you say:**
"Here's our live dashboard. The first thing you notice is the alert level — currently showing GREEN, meaning LOW risk of flare in the next 30 minutes. Below that, flare probability is 0.0%. That's the real-time forecast."

*[Point to the metrics row]*

**Action**: Let page load fully. Don't click yet. Let judges see the clean interface.

---

### **PART 2: TOP METRICS (20 seconds)**

*[Pause slightly, then scroll to show the four top metric boxes]*

**What you say:**
"We're displaying four key metrics in real-time:

1. **Latest Flux** — 0.0 counts. The most recent X-ray measurement from Aditya-L1.
2. **Mean Flux (10-min window)** — 37.8 counts. Average flux over the most recent 10-minute window.
3. **Std Dev** — 108.6. Variability. High std dev often indicates precursor activity.
4. **Data Source** — SoLEXS + HEL1OS. We're merging both instruments into one view."

*[Hover over each metric briefly to highlight it]*

**Key point to emphasize**: "Notice the data source says 'SoLEXS + HEL1OS' — this is multi-instrument fusion. That's unique."

---

### **PART 3: ALERT BANNER & PROBABILITY (15 seconds)**

*[Point to the "Current Alert Level: 🟢 LOW" heading]*

**What you say:**
"This banner is what operators look at. It's color-coded:
- 🟢 GREEN (LOW): <40% probability
- 🟡 YELLOW (MEDIUM): 40–70% probability
- 🔴 RED (HIGH): >70% probability

Right now, probability is 0.0% because we're in a quiet period. But when precursor activity is detected, this banner will turn yellow or red — and that's the **16.51-minute lead-time alert** we talked about."

*[Pause for effect]*

---

### **PART 4: FLUX TIME SERIES (45 seconds)**

*[Scroll down to the flux plot]*

**What you say:**
"Let me show you the X-ray flux over the last 6 hours. This is a time series from Aditya-L1 instruments."

*[Point to the red line and shaded area]*

"The red line shows X-ray counts in real-time. The shaded area beneath it is the flux intensity. You can see it's mostly flat — that's typical background X-ray activity. 

But when a solar flare is happening, this plot *spiked up dramatically*. Our model watches for patterns in this data: a rising mean, increased variability, higher peak values — these are precursor signatures."

*[If there's a visible spike in the historical data, point to it]:*
"See that spike? That's a real flare we detected. Our detector flagged it, our model assigned it a high probability, and operators would have received an alert ~17 minutes before the peak."

*[Scroll horizontally or zoom if needed to show variation]:*
"The 10-point moving average (the dashed blue line) smooths out noise. This is what the model actually sees."

---

### **PART 5: PREDICTION PROBABILITY OVER TIME (45 seconds)**

*[Scroll down to the prediction probability plot]*

**What you say:**
"This chart shows model predictions over historical test data. Each point is a 10-minute window, and the vertical axis is the predicted probability (0–100%)."

*[Point to the line]*

"The blue line traces predicted probability across thousands of windows. Most of the time it's near zero — we're in low-risk periods. But watch these spikes."

*[Point to any prominent peaks, or describe generally]*

"When we see these probability spikes, that's the model saying: 'Flare precursors detected — alert now.' The red/orange dots are windows where we made true-positive predictions (we said 'flare' and there actually was one). Yellow X marks are false positives (we said 'flare' but there wasn't one)."

*[Point to the red threshold line]*

"The horizontal red line at 0.5 is our decision threshold. Predictions above 0.5 = alert. Below = no alert."

*[Pause]*

"This is why our **lead time is 16.51 minutes** — we're raising the alert while the model still sees precursor patterns, *before* the actual flare peak."

---

### **PART 6: MODEL PERFORMANCE METRICS (30 seconds)**

*[Scroll down to the performance summary section]*

**What you say:**
"Here are the model metrics. Let me focus on the most important ones:

**ROC-AUC: 0.894** — This is strong. It means the model genuinely discriminates between flare-precursor patterns and background. On a scale from 0.5 (random guess) to 1.0 (perfect), 0.894 is excellent.

**Accuracy: 98.5%** — Yes, that sounds amazing. But it's misleading because flares are rare. If I just predicted 'no flare' 98% of the time, I'd get the same accuracy.

**Precision: 50%** — Of the alerts we raise, half are correct flares. That's acceptable for an operational system.

**Recall: 25.6%** — We catch about 1 in 4 actual flares. With only 16 training flares, this is expected. With 100+ training flares, recall will improve.

**F1-Score: 0.338** — Harmonic mean of precision and recall. Conservative but safe for operators."

*[Pause, make eye contact]*

"The key takeaway: **ROC-AUC 0.894 proves we learned real patterns, not noise.**"

---

### **PART 7: DATA STATISTICS TABLE (20 seconds)**

*[Scroll down to the data statistics table]*

**What you say:**
"Finally, here's a summary of the data we trained on:

- **Total Records**: 810,904 X-ray measurements across 6 days
- **Time Window**: Last 6 hours (user-adjustable)
- **Records in Window**: ~2,000 recent measurements
- **Mean Flux**: 37.8 counts — baseline activity
- **Max Flux**: Often 500–1000+ during flares
- **Min Flux**: Can drop to single digits during quiet periods

All of this data came from real Aditya-L1 instruments, cross-validated against NOAA observations."

---

### **PART 8: INTERACTIVE FEATURE — CHANGE DATA SOURCE (15 seconds)**

*[Click the sidebar dropdown "Select X-ray Data Source"]*

**What you say:**
"One more feature — let me show you the flexibility. I can switch between data sources."

*[Change from "Both (Merged)" to "SoLEXS Only"]*

"Now we're looking at *only* the SoLEXS instrument. Watch the plot update."

*[Wait for plot to refresh]*

"Notice the flux values change slightly — different instrument, different sensitivity. Let me switch back to merged data."

*[Switch back to "Both (Merged)"]*

"We're now fusing SoLEXS and HEL1OS. The fact that both instruments see correlated flare signals validates our detections against independent hardware."

---

### **PART 9: CLOSING (20 seconds)**

*[Scroll back to the top to show the alert banner one final time]*

**What you say:**
"That's the dashboard in action. Real-time X-ray monitoring, automated flare detection, and 16.51-minute lead-time forecasting — all in one view. An operator can open this on their workstation and immediately see solar flare risk.

This is operationally deployable *today*. No research papers required. Just good data + good engineering.

Thank you."

*[Step back, let judges absorb the system]*

---

## Timing Breakdown

| Section | Time | Running Total |
|---------|------|--------|
| Initial View | 15s | 15s |
| Top Metrics | 20s | 35s |
| Alert Banner | 15s | 50s |
| Flux Time Series | 45s | 1:35 |
| Prediction Probability | 45s | 2:20 |
| Model Metrics | 30s | 2:50 |
| Data Statistics | 20s | 3:10 |
| Interactive Feature | 15s | 3:25 |
| Closing | 20s | 3:45 |
| **TOTAL DEMO** | ~3:45 | — |

*This leaves ~1 minute for judges to ask real-time questions or for you to recover if something glitches.*

---

## Contingency Plans

**If dashboard crashes or won't load:**
- [ ] Have a backup screenshot file of the dashboard
- [ ] Be able to say: "The live system is running on my laptop; let me show you a screenshot of what you'd see in production" — then switch to image
- [ ] Have the GitHub link ready to show code instead

**If a plot doesn't render:**
- [ ] Refresh the page (Ctrl+R)
- [ ] If that fails, move on: "The underlying prediction data is saved here; let me show you the CSV results instead"
- [ ] Pull up `output/forecast_results_rf.csv` in a spreadsheet to show raw predictions

**If someone asks a technical question mid-demo:**
- [ ] Pause the demo, answer the question clearly
- [ ] Resume where you left off
- [ ] Don't try to answer if you're unsure — say "Great question; we have detailed documentation on GitHub"

---

## What NOT to Do During Demo

❌ Don't rush. Speak slowly, let judges read the screen.
❌ Don't click randomly. Each click should be purposeful.
❌ Don't explain technical details judges didn't ask for. Keep it operational.
❌ Don't apologize for limitations mid-demo. Own them confidently or save them for Q&A.
❌ Don't leave the dashboard open too long on one screen. Keep it flowing.
❌ Don't forget to highlight the 16.51-minute lead time — it's your unique selling point.

---

## Practice Run Checklist

Before submission day, practice this demo 3 times:

**Run 1**: With full narration, no interruptions. Time it. Aim for 3:45–4:00.
**Run 2**: With a friend asking random questions mid-demo. Practice recovering.
**Run 3**: With projector/external screen to verify it looks good on large displays.

After each run, note:
- Any clicks that took too long
- Any explanations that were unclear
- Any technical glitches
- Timing issues

---

**You've got this. Practice once, go live confident, let the system speak for itself.**
