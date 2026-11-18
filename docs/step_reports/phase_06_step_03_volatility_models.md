# Step Report: Phase 6 — Step 6.3: Volatility Forecasting & Clustering

**Document ID**: `docs/step_reports/phase_06_step_03_volatility_models.md`  
**Phase**: Phase 6 — Machine Learning & Statistical Modeling  
**Step**: Step 6.3 — Volatility Forecasting & Clustering (`models/statistical/volatility_models.py`)  
**Status**: APPROVED / COMPLETED  
**Date**: 2026-11-17  

---

## 1. Objective & Business Relevance
- **Objective**: Implement time-varying conditional volatility forecasting models (`models/statistical/volatility_models.py`) to capture the volatility clustering effects ($\rho_1(r^2) > 0.15$) discovered in Phase 5 EDA:
  - **RiskMetrics EWMA Volatility**: Recursive exponentially weighted moving average ($\lambda = 0.94$):
    $$\sigma_t^2 = \lambda \sigma_{t-1}^2 + (1 - \lambda) r_{t-1}^2$$
  - **GARCH(1,1) Conditional Volatility Model**:
    $$\sigma_t^2 = \omega + \alpha r_{t-1}^2 + \beta \sigma_{t-1}^2, \quad \text{with } \alpha + \beta < 1$$
  - **Dynamic Volatility Bands**: Dynamic price envelopes scaling anomaly thresholds according to macro volatility regimes.
- **Business Relevance**: Fixed historical standard deviation thresholds create excessive false positives during market-wide turmoil (e.g. macro shocks) and miss subtle abnormal trades during low-volatility consolidation periods. Dynamic conditional volatility models adapt thresholds to market regimes, maintaining extreme sensitivity when stocks are calm and widening tolerance when market noise is elevated.

---

## 2. Technical Explanation & Architectural Fit
- **EWMA Volatility Forecaster (`EWMAVolatilityForecaster`)**:
  - Uses standard RiskMetrics parameter $\lambda = 0.94$.
  - Recursive update computes annualized conditional volatility $\sigma_t \times \sqrt{252}$ without forward data leakage.
- **GARCH(1,1) Optimizer (`GARCHVolatilityModel`)**:
  - Maximum likelihood estimation under Gaussian error assumptions.
  - Constrained optimization enforcing parameter non-negativity and covariance stationarity ($\alpha + \beta < 0.999$).
  - Built-in fallback to calibrated empirical parameters ($\omega=0.04\sigma^2, \alpha=0.08, \beta=0.88$) for short time-series (< 25 days).
- **Dynamic Volatility Bands (`DynamicVolatilityBandGenerator`)**:
  - Generates regime-adaptive envelopes around prior closing price:
    $$P_{\text{Upper}} = P_{t-1} \times (1 + k \cdot \sigma_{t, \text{daily}})$$
    $$P_{\text{Lower}} = P_{t-1} \times (1 - k \cdot \sigma_{t, \text{daily}})$$

---

## 3. Technology Decisions & Alternatives Considered
- **Numerical SLSQP Optimizer vs External C-Extensions**:
  - Utilized `scipy.optimize.minimize` (SLSQP with bounds and linear inequality constraints) to eliminate brittle external binary dependencies while running in sub-second CPU time.
- **RiskMetrics EWMA Integration**:
  - EWMA offers zero-fitting instant evaluation for real-time streaming pipelines, while GARCH(1,1) provides deep econometric modeling for batch surveillance.

---

## 4. Files Created / Modified
- `models/statistical/volatility_models.py`: EWMA and GARCH(1,1) volatility models and dynamic band generator.
- `tests/unit/test_volatility_models.py`: Automated unit tests (4 test cases) verifying EWMA updates, GARCH stationarity, dynamic envelope scaling, and empty input handling.
- `docs/step_reports/phase_06_step_03_volatility_models.md`: Step documentation and operational guidelines.
- `docs/PROJECT_TRACKER.md`: Updated Step 6.3 status to `COMPLETED`.
- `docs/CHANGELOG.md`: Logged Step 6.3 completion.

---

## 5. Commands Executed & Testing Report
- **Command**: `python -m pytest tests/unit/test_volatility_models.py -v`
  - Output: `4 passed in 1.45s`
- **Command**: `python -m pytest tests/ -v`
  - Output: `76 passed in 6.26s` across all 76 repository test cases.

---

## 6. Known Limitations, Risks & Edge Cases
- **Optimization Non-Convergence**: If returns exhibit extreme discontinuities, MLE optimization may fail to converge; the class gracefully catches warnings and falls back to stationary calibrated parameters.

---

## 7. Status & Next Step
- **Step 6.3 Status**: COMPLETED & VERIFIED.
- **Proposed Next Step**: Proceed to **Phase 6 — Step 6.4: Chronological Walk-Forward Validation Framework** (`models/validation/walk_forward.py` strictly enforcing expanding/rolling temporal splits to eliminate test set contamination).
