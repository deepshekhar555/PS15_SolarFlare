# Quick Start Guide - Solar Flare Forecasting Dashboard

## Installation (Already Done ✓)
- scikit-learn 1.9.0
- joblib 1.5.3
- streamlit 1.58.0
- matplotlib

## Running the Dashboard

From the workspace root (`d:\PS15_SolarFlare`), run:

```bash
streamlit run dashboard.py
```

This will:
1. Start a local Streamlit server (typically on `http://localhost:8501`)
2. Automatically open in your default browser
3. Display real-time X-ray flux plots and flare probability predictions

## Dashboard Features

### Controls (Sidebar)
- **Data Source Selector**: Choose SoLEXS, HEL1OS, or both
- **Time Window Slider**: Adjust historical window (1-24 hours)

### Main Display
- **Alert Banner**: Real-time flare probability and alert level (LOW/MEDIUM/HIGH)
- **Flux Time Series**: X-ray counts over selected window with 10-point moving average
- **Predictions Over Time**: Historical predictions showing true/false positives
- **Model Performance Summary**: Key metrics (Accuracy, Precision, Recall, F1, ROC-AUC, Lead Time)
- **Data Statistics Table**: Summary statistics for current view

## Key Results to Present

✅ **Model Performance**
- ROC-AUC: 0.894 (strong discrimination)
- Average Lead Time: 16.51 minutes (ISRO evaluation criterion)

✅ **Data**
- 6 days of Aditya-L1 observations (June 13–18, 2026)
- 14,139 labeled windows from SoLEXS + HEL1OS
- 16 real solar flare events detected

✅ **Real-Time Capability**
- Dashboard updates with latest flux data
- Instantaneous probability scoring
- Actionable alert levels for operators

## Files Generated

1. **Model**: `output/forecast_model_rf.joblib`
2. **Predictions**: `output/forecast_results_rf.csv`
3. **Summary**: `output/MODEL_SUMMARY.md`
4. **Dashboard**: `dashboard.py`

---

**Status**: Outcome #2 (forecasting model) ✅ COMPLETE | Outcome #3 (dashboard) ✅ COMPLETE

**Next Step**: Deploy to cloud (optional) or prepare demo for ISRO submission.
