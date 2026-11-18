# Step Report: Phase 6 — Step 6.2: Machine Learning Anomaly Detection (Isolation Forest)

**Document ID**: `docs/step_reports/phase_06_step_02_isolation_forest.md`  
**Phase**: Phase 6 — Machine Learning & Statistical Modeling  
**Step**: Step 6.2 — Machine Learning Anomaly Detection (`models/ml/isolation_forest_detector.py`)  
**Status**: APPROVED / COMPLETED  
**Date**: 2026-11-17  

---

## 1. Objective & Business Relevance
- **Objective**: Implement the machine learning anomaly detection engine (`models/ml/isolation_forest_detector.py`) using unsupervised Isolation Forests (`sklearn.ensemble.IsolationForest`) to isolate multi-dimensional, non-linear market anomalies across quantitative returns, volatility, volume, and news divergence features:
  - Multi-feature surveillance vector (`log_return_1d`, `volatility_20d`, `parkinson_volatility_20d`, `volume_zscore_20d`, `delivery_ratio`, `news_price_divergence`, `volume_news_divergence`).
  - Robust scaling (`RobustScaler`) resistant to historical outliers.
  - Sigmoid-transformed continuous decision score bounded strictly in $[0.0, 1.0]$.
  - Heuristic feature attribution identifying the principal feature driving each anomaly.
- **Business Relevance**: Insider trading schemes and complex market manipulation strategies frequently split trades to evade simple linear 3-sigma thresholds. A stock experiencing a $+1.9\%$ price move with a $+2.1\sigma$ volume surge and a low $12\%$ delivery ratio in a news vacuum may avoid individual Z-score triggers but represents an extreme multi-dimensional anomaly. Isolation Forest identifies these subtle multi-factor clusters with high precision.

---

## 2. Technical Explanation & Architectural Fit
- **Algorithm & Hyperparameters**:
  - `n_estimators`: 100 trees (fast CPU evaluation on Windows 11 host).
  - `contamination`: 0.02 (empirically calibrated to flag top $2\%$ extreme market regimes).
  - `n_jobs`: -1 (clean multithreaded CPU utilization).
- **Normalized Anomaly Score**:
  - Raw path length decision function $s(x)$ is transformed into continuous $[0.0, 1.0]$ scores:
    $$\text{Score} = \frac{1}{1 + e^{5 \cdot s(x)}}$$
    where $1.0$ represents the most isolated multidimensional anomaly and $0.0$ represents dense inliers.
- **Feature Attribution Engine**:
  - Evaluates the absolute scaled deviation across the input vector to pinpoint the primary metric responsible for tree isolation.

---

## 3. Technology Decisions & Alternatives Considered
- **Isolation Forest vs One-Class SVM / Autoencoders**:
  - One-Class SVM scales poorly ($O(N^2)$ to $O(N^3)$) with historical market data and is sensitive to kernel choices. Deep Autoencoders require heavy PyTorch/GPU overhead. Isolation Forest scales linearly ($O(N \log N)$), requires no GPU, and offers exceptional empirical performance on tabular financial features.
- **RobustScaler vs StandardScaler**:
  - `StandardScaler` calculates mean and variance which are heavily distorted by extreme financial shocks (fat tails); `RobustScaler` uses medians and interquartile ranges (IQR), preserving outlier isolation.

---

## 4. Files Created / Modified
- `models/ml/isolation_forest_detector.py`: Isolation Forest anomaly detection engine (`IsolationForestAnomalyDetector`).
- `tests/unit/test_isolation_forest.py`: Automated unit tests (4 test cases) verifying initialization, training, score normalization, feature attribution, and error handling.
- `docs/step_reports/phase_06_step_02_isolation_forest.md`: Step documentation and operational guidelines.
- `docs/PROJECT_TRACKER.md`: Updated Step 6.2 status to `COMPLETED`.
- `docs/CHANGELOG.md`: Logged Step 6.2 completion.

---

## 5. Commands Executed & Testing Report
- **Command**: `python -m pytest tests/unit/test_isolation_forest.py -v`
  - Output: `4 passed in 2.85s`
- **Command**: `python -m pytest tests/ -v`
  - Output: `72 passed in 5.95s` across all 72 repository test cases.

---

## 6. Known Limitations, Risks & Edge Cases
- **Cold Start Warmup**: Requires a minimum of 10 historical records to fit trees; cold-start datasets return an unfitted warning rather than crashing.

---

## 7. Status & Next Step
- **Step 6.2 Status**: COMPLETED & VERIFIED.
- **Proposed Next Step**: Proceed to **Phase 6 — Step 6.3: Volatility Forecasting & Clustering** (`models/statistical/volatility_models.py` implementing rolling EWMA and GARCH(1,1) volatility models for conditional risk bounds).
