# Step Report: Phase 6 — Step 6.1: Statistical Baseline Anomaly Detection

**Document ID**: `docs/step_reports/phase_06_step_01_statistical_baseline.md`  
**Phase**: Phase 6 — Machine Learning & Statistical Modeling  
**Step**: Step 6.1 — Statistical Baseline Anomaly Detection (`models/statistical/baseline_detector.py`)  
**Status**: APPROVED / COMPLETED  
**Date**: 2026-11-17  

---

## 1. Objective & Business Relevance
- **Objective**: Implement the deterministic statistical baseline anomaly detection engine (`models/statistical/baseline_detector.py`) establishing empirical reference benchmarks for market surveillance before introducing complex machine learning models:
  - Rolling Z-score anomaly bounds for 1-day return ($Z_{\text{ret}}$) and 20-day volume ($Z_{\text{vol}}$) using causal historical windows.
  - Empirical non-parametric percentile thresholds ($95\text{th}$, $99\text{th}$, and $99.9\text{th}$ percentiles) calibrated to accommodate the fat tails and leptokurtosis proven in Step 5.1 EDA.
  - Delivery divergence anomaly detection: flagging high volume surges ($Z_{\text{vol}} \ge 2.5$) accompanied by low delivery percentages ($\le 30\%$), indicative of speculative churn or wash trading.
  - Anomaly classification outputs: severity level (`NORMAL`, `WATCHLIST`, `SUSPICIOUS`, `ALERT`) and statistical anomaly score bounded in $[0.0, 1.0]$.
- **Business Relevance**: Production surveillance platforms require transparent, explainable statistical baselines. In regulated environments (SEBI/SEC), simple statistical bounds (e.g. 3-sigma or 99th percentile moves) provide an empirical benchmark against which machine learning algorithms (Isolation Forest in Step 6.2) must be evaluated.

---

## 2. Technical Explanation & Architectural Fit
- **Statistical Scoring Formulation**:
  - `statistical_anomaly_score`: Weighted mixture bounded in $[0.0, 1.0]$:
    $$\text{Score} = 0.35 \times \min\left(1.0, \frac{|Z_{\text{ret}}|}{4.0}\right) + 0.35 \times \min\left(1.0, \frac{Z_{\text{vol}}}{4.0}\right) + 0.20 \times \text{Flag}_{\text{deliv\_divergence}} + 0.10 \times \text{Flag}_{\text{unbacked}}$$
- **Categorical Severity Tiering**:
  - `ALERT`: Score $\ge 0.70$ or concurrent $(|Z_{\text{ret}}| \ge 3.0 \land Z_{\text{vol}} \ge 3.0)$.
  - `SUSPICIOUS`: Score $\ge 0.45$.
  - `WATCHLIST`: Score $\ge 0.25$.
  - `NORMAL`: Score $< 0.25$.
- **Empirical Calibration (`fit`)**:
  - Calculates non-parametric percentiles ($P_{95}, P_{99}, P_{99.9}$) directly from historical data, avoiding Gaussian normality assumptions on leptokurtic distributions.

---

## 3. Technology Decisions & Alternatives Considered
- **Non-Parametric Percentiles vs Parametric Gaussian Cutoffs**:
  - Equity returns exhibit heavy tails (kurtosis $> 2.5$). Standard Gaussian $3\sigma$ cutoffs assume normal tails and underestimate tail probability by orders of magnitude; empirical percentiles provide accurate risk calibration.
- **Delivery Divergence Integration**:
  - High volume with low delivery is a known signal for pump-and-dump or spoofing; directly embedding it in the baseline score provides high surveillance precision.

---

## 4. Files Created / Modified
- `models/statistical/baseline_detector.py`: Statistical baseline anomaly detection engine (`StatisticalBaselineDetector`).
- `tests/unit/test_statistical_baseline.py`: Automated unit tests (3 test cases) validating fit calibration, scoring, tiering, delivery divergence, and boundary safety.
- `docs/step_reports/phase_06_step_01_statistical_baseline.md`: Step documentation and operational guidelines.
- `docs/PROJECT_TRACKER.md`: Updated Step 6.1 status to `COMPLETED`.
- `docs/CHANGELOG.md`: Logged Step 6.1 completion.

---

## 5. Commands Executed & Testing Report
- **Command**: `python -m pytest tests/unit/test_statistical_baseline.py -v`
  - Output: `3 passed in 1.26s`
- **Command**: `python -m pytest tests/ -v`
  - Output: `68 passed in 7.79s` across all 68 repository test cases.

---

## 6. Known Limitations, Risks & Edge Cases
- **Fixed Linear Weights**: Baseline linear scoring weights ($0.35 / 0.35 / 0.20 / 0.10$) provide transparent explainability but cannot capture non-linear feature interactions; this is addressed by the machine learning Isolation Forest detector in Step 6.2.

---

## 7. Status & Next Step
- **Step 6.1 Status**: COMPLETED & VERIFIED.
- **Proposed Next Step**: Proceed to **Phase 6 — Step 6.2: Machine Learning Anomaly Detection (Isolation Forest)** (`models/ml/isolation_forest_detector.py` implementing unsupervised isolation trees with contamination tuning and SHAP feature attribution).
