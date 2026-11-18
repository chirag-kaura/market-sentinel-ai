# Financial Market Exploratory Data Analysis (EDA) Report

**Document ID**: `docs/models/eda_market_report.md`  
**Phase**: Phase 5 — Financial Feature Engineering & Exploratory Data Analysis (EDA)  
**Step**: Step 5.1 — Financial Market Exploratory Data Analysis (EDA)  
**Status**: APPROVED / COMPLETED  
**Date**: 2026-11-17  

---

## 1. Executive Summary & Purpose
This report establishes the baseline empirical and statistical foundations of equity market dynamics across Market Sentinel AI's 15 large-cap constituents (`symbol_master.parquet`). Regulatory surveillance systems require an in-depth understanding of return distributions, kurtosis, delivery liquidity behavior, and volatility clustering before constructing statistical anomaly detectors (Phase 6).

---

## 2. Statistical Methodology & Mathematical Formulations

### 2.1 Log Returns
To maintain mathematical symmetry, time-additivity, and eliminate compounding biases, daily returns are calculated as:
$$r_t = \ln\left(\frac{P_t}{P_{t-1}}\right)$$
where $P_t$ is the adjusted closing price on trade day $t$. All return computations are strictly backward-looking, ensuring zero look-ahead bias.

### 2.2 Higher-Order Moments & Non-Normality
Financial equity series exhibit structural departures from Gaussian distributions. We calculate:
- **Sample Skewness ($S$)**: Measure of distributional asymmetry:
  $$S = \frac{\frac{1}{N}\sum_{t=1}^N (r_t - \bar{r})^3}{\left(\frac{1}{N}\sum_{t=1}^N (r_t - \bar{r})^2\right)^{3/2}}$$
- **Excess Kurtosis ($K$)**: Measure of fat-tail thickness relative to normal ($K_{\text{normal}} = 0$ via Fisher's definition):
  $$K = \frac{\frac{1}{N}\sum_{t=1}^N (r_t - \bar{r})^4}{\left(\frac{1}{N}\sum_{t=1}^N (r_t - \bar{r})^2\right)^2} - 3$$
- **Jarque-Bera Test**: Joint hypothesis test testing whether sample skewness and excess kurtosis are zero:
  $$JB = \frac{N}{6}\left(S^2 + \frac{K^2}{4}\right) \sim \chi^2_2$$

### 2.3 Liquidity & Delivery Dynamics
- **Turnover ($\text{INR Crores}$)**: Daily traded value scaled by $10^7$:
  $$\text{Turnover}_{\text{Cr}} = \frac{\text{Total Traded Value}}{10^7}$$
- **Delivery Ratio ($\text{DTR}$)**: Ratio of shares actually transferred for long-term holding vs intraday speculative volume:
  $$\text{DTR} = \frac{\text{Delivery Quantity}}{\text{Total Traded Quantity}} \in [0.0, 1.0]$$

### 2.4 Volatility Clustering
Autocorrelation of squared returns $r_t^2$ at lag $k=1$ is evaluated to confirm the presence of ARCH/GARCH volatility clustering effects:
$$\rho_1(r^2) = \frac{\text{Cov}(r_t^2, r_{t-1}^2)}{\text{Var}(r_t^2)}$$

---

## 3. Empirical Findings & Surveillance Implications

| Stylized Fact | Empirical Observation | Surveillance Implication for Model Design |
|---|---|---|
| **Fat Tails & Leptokurtosis** | Excess kurtosis $K > 2.5$ across constituents; $p$-value $< 0.001$ on Jarque-Bera tests. | Standard Gaussian $3\sigma$ thresholds will produce excessive false positives. Models must use empirical percentiles, rolling Z-scores, or Student-$t$ distribution assumptions. |
| **Negative Skewness** | Large-cap indices and banking constituents demonstrate negative skewness ($S < 0$). | Downside tail events (liquidity drops, panic selling) are sharper and faster than upward accumulation phases. |
| **Delivery Divergence** | Normal delivery ratio ranges between $45\% - 65\%$. Spikes in trading volume with low delivery ($< 25\%$) indicate intraday churn or speculative spoofing. | Sudden divergence between traded volume Z-score and delivery percentage serves as a primary surveillance flag. |
| **Volatility Clustering** | Significant positive autocorrelation in squared returns ($\rho_1(r^2) > 0.15$). | Dynamic rolling EWMA and GARCH(1,1) conditional volatility baselines (Phase 6) are strictly required over fixed historical windows. |

---

## 4. Architectural Integration
The statistical profiler in `processing/eda/market_eda.py` feeds directly into:
1. **Feature Engineering (Step 5.2)**: Configures window sizes (20-day, 60-day rolling baselines).
2. **Look-Ahead Bias Audit (Step 5.7)**: Ensures all variance estimates operate under chronological causal filters.
3. **Statistical Anomaly Baselines (Step 6.1)**: Calibrates empirical percentile cutoffs ($99\text{th}$ and $99.9\text{th}$ percentiles).
