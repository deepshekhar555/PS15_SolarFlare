# Solar Flare Nowcasting & Forecasting Model Summary

## Outcome #2: Forecasting Model Results

### Model Specification
- **Type**: RandomForest Classifier
- **Configuration**: 200 estimators, `class_weight='balanced'` (addresses class imbalance)
- **Features**: 5 (mean, std, max, last, slope of X-ray flux counts in 10-minute windows)
- **Training Data**: Combined SoLEXS + HEL1OS X-ray flux time series (June 13–18, 2026)
- **Window Strategy**: Sliding 10-minute windows with 60-second step

### Training Data Summary
- **Total windows**: 14,139
- **Positive windows** (flare in next 30 min): 213 (1.51%)
- **Negative windows**: 13,926 (98.49%)
- **Real flare events detected**: 16
- **Test/train split**: 80/20 with stratification

### Performance Metrics (Time-Based Holdout — Leakage-Free)
| Metric | Value | Notes |
|--------|-------|-------|
| Accuracy | 0.955 | Misleading — class imbalance (120 pos vs 2708 neg in test) |
| Precision | 0.125 | 1 in 8 positive predictions is a real flare |
| Recall | 0.008 | Model catches ~1% of flares on time-based test |
| F1-Score | 0.016 | Low due to extreme imbalance and small sample |
| ROC-AUC | **0.533** | Near-random — honest leakage-free result |

### Lead Time (ISRO Evaluation Criterion)
- **Average lead time for true positives**: **4.57 minutes** (time-based, honest)
- **Interpretation**: With only 16 training events in a 6-day window, the model has insufficient positive examples to learn reliable precursor patterns

### Model Assessment
- **This is a Phase 1 proof-of-concept prototype only.** With 16 flare events, no ML model can achieve meaningful precision/recall.
- The ROC-AUC of 0.533 (barely above random) is the *correct expected result* for this sample size.
- A historical random-stratified split previously reported ROC-AUC ~0.894 and Precision 50%, but that evaluation had temporal leakage from overlapping windows and is not a valid performance estimate.
- **To improve**: Ingest multi-month Aditya-L1 archives (100–150+ flare events) and retrain.

### Files
- Model: `output/forecast_model_rf.joblib` (joblib format)
- Predictions: `output/forecast_results_rf.csv` (window-level predictions with probabilities)

### Next Phase
Moving to **Outcome #3**: Interactive Streamlit dashboard displaying:
- Live X-ray flux time series plots
- Real-time flare probability scores
- Alert levels (LOW/MEDIUM/HIGH)
