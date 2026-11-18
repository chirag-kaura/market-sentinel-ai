# Comprehensive Feature Dictionary: Market Sentinel AI

**Document ID**: `docs/data/feature_dictionary.md`  
**Phase**: Phase 5 — Financial Feature Engineering & Exploratory Data Analysis (EDA)  
**Step**: Step 5.6 — Comprehensive Feature Dictionary  
**Status**: APPROVED / COMPLETED  
**Date**: 2026-11-17  
**Master Implementation Directive**: [`docs/MASTER_IMPLEMENTATION_PROMPT.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/MASTER_IMPLEMENTATION_PROMPT.md)  

---

## 1. Overview & Purpose
This Feature Dictionary defines the definitive metadata, mathematical formulas, temporal lookback windows, and regulatory rationale for all engineered quantitative market features, textual news signals, and cross-modal interaction indicators in **Market Sentinel AI**. Every feature is strictly causal (backward-looking) with zero look-ahead bias, ensuring compliance with SEBI, SEC, and international model risk management standards.

---

## 2. Feature Master Catalog

### Family 1: Price Dynamics & Cumulative Returns
| Feature Name | Data Type | Formula / Definition | Lookback | Range / Bounds | Surveillance & Regulatory Rationale |
|---|---|---|---|---|---|
| `log_return_1d` | `float64` | $\ln\left(\frac{Close_t}{Close_{t-1}}\right)$ | 1 day | $[-0.30, +0.30]$ | Immediate intraday price momentum; detects sharp single-day spikes or collapses. |
| `log_return_5d` | `float64` | $\ln\left(\frac{Close_t}{Close_{t-5}}\right)$ | 5 days | $[-0.50, +0.50]$ | Multi-day short-term momentum; captures accumulation trends ahead of public announcements. |
| `log_return_20d` | `float64` | $\ln\left(\frac{Close_t}{Close_{t-20}}\right)$ | 20 days | $[-0.80, +0.80]$ | Monthly medium-term trend; establishes baseline price velocity for trend-breakout detection. |
| `proximity_to_52w_high` | `float64` | $\frac{Close_t}{\max_{i \in [t-251, t]} High_i}$ | 252 days | $(0.0, 1.05]$ | Proximity to 52-week high; identifies potential breakout manipulation or distribution traps near multi-month peaks. |
| `proximity_to_52w_low` | `float64` | $\frac{Close_t}{\min_{i \in [t-251, t]} Low_i}$ | 252 days | $[1.0, 5.0)$ | Proximity to 52-week low; flags distress sell-offs or predatory short-selling near multi-month bottoms. |

---

### Family 2: Volatility & Extreme Dispersion
| Feature Name | Data Type | Formula / Definition | Lookback | Range / Bounds | Surveillance & Regulatory Rationale |
|---|---|---|---|---|---|
| `volatility_20d` | `float64` | $\text{std}(r_{1d}, 20) \times \sqrt{252}$ | 20 days | $[0.05, 1.50]$ | Close-to-close annualized volatility; baseline risk metric for regime shifts. |
| `parkinson_volatility_20d` | `float64` | $\sqrt{\frac{1}{4 \ln 2 \cdot 20} \sum_{i=1}^{20} \left(\ln\frac{High_i}{Low_i}\right)^2} \times \sqrt{252}$ | 20 days | $[0.05, 2.00]$ | Extreme-value intraday dispersion; 5x higher efficiency than close-to-close volatility on EOD data. |

---

### Family 3: Volume Dynamics & Liquidity Behavior
| Feature Name | Data Type | Formula / Definition | Lookback | Range / Bounds | Surveillance & Regulatory Rationale |
|---|---|---|---|---|---|
| `volume_mean_20d` | `float64` | $\frac{1}{20}\sum_{i=1}^{20} Volume_{t-i+1}$ | 20 days | $[10^3, 10^9]$ | Rolling volume baseline; benchmarks typical market participation per equity. |
| `volume_zscore_20d` | `float64` | $\frac{Volume_t - \mu_{V, 20}}{\sigma_{V, 20}}$ | 20 days | $[-3.0, +10.0+]$ | Standardized volume anomaly score; $Z > +3.0$ signals extreme volume bursts characteristic of front-running. |
| `delivery_ratio` | `float64` | $\frac{\text{Delivery Qty}_t}{\text{Total Traded Qty}_t}$ | 1 day | $[0.0, 1.0]$ | Ratio of shares transferred to depository; separates genuine investment from speculative intraday churn. |
| `delivery_ratio_zscore_20d`| `float64` | $\frac{\text{DTR}_t - \mu_{\text{DTR}, 20}}{\sigma_{\text{DTR}, 20}}$ | 20 days | $[-4.0, +4.0]$ | Standardized shift in delivery intent; sudden negative drop with volume spike flags speculative wash trading. |

---

### Family 4: News Arrival & Corporate Disclosure Signals
| Feature Name | Data Type | Formula / Definition | Lookback | Range / Bounds | Surveillance & Regulatory Rationale |
|---|---|---|---|---|---|
| `news_count_1d` | `int64` | $\sum \mathbf{1}_{\text{article published before 15:30 IST on date } t}$ | 1 day | $[0, 50+]$ | Daily verified news frequency; measures public media attention. |
| `news_count_3d` | `int64` | $\sum_{i=0}^2 \text{news\_count}_{t-i}$ | 3 days | $[0, 150+]$ | Short-term media narrative persistence; captures multi-day media cycles. |
| `news_count_7d` | `int64` | $\sum_{i=0}^6 \text{news\_count}_{t-i}$ | 7 days | $[0, 300+]$ | Weekly media exposure; benchmarks medium-term public visibility. |
| `news_velocity_zscore_30d` | `float64` | $\frac{\text{news\_count}_{1d} - \mu_{\text{news}, 30}}{\sigma_{\text{news}, 30} + \epsilon}$ | 30 days | $[-2.0, +8.0+]$ | Symbol-relative news velocity anomaly; eliminates media coverage bias between mega-caps and smaller stocks. |
| `disclosure_count_1d` | `int64` | Official regulatory filings on trade date $t$ | 1 day | $[0, 10+]$ | Frequency of official regulatory communications under SEBI LODR. |
| `has_financial_results` | `int64` | $\mathbf{1}_{\text{Earnings / Q1-Q4 / Audited Results Filing}}$ | 1 day | $\{0, 1\}$ | High-impact earnings catalyst; provides legitimate rationale for sharp price adjustments. |
| `has_board_meeting` | `int64` | $\mathbf{1}_{\text{Board Meeting Notice (Dividends, Bonus, Strategy)}}$ | 1 day | $\{0, 1\}$ | Formal governance event; scheduled disclosure window. |
| `has_mna_filing` | `int64` | $\mathbf{1}_{\text{Mergers, Acquisitions, Joint Ventures}}$ | 1 day | $\{0, 1\}$ | Major corporate structural action; high-risk trigger for insider leakage investigations. |
| `has_compliance_action` | `int64` | $\mathbf{1}_{\text{SEBI / Exchange Penalty, Insider PIT Form C/D}}$ | 1 day | $\{0, 1\}$ | Regulatory enforcement or insider trade declaration filing. |
| `avg_sentiment_polarity_1d`| `float64` | Lexicon polarity $\frac{\text{Pos} - \text{Neg}}{\text{Pos} + \text{Neg}}$ | 1 day | $[-1.0, +1.0]$ | Daily average sentiment direction of media headlines and summaries. |

---

### Family 5: Cross-Modal Surveillance Interaction Features
| Feature Name | Data Type | Formula / Definition | Lookback | Range / Bounds | Surveillance & Regulatory Rationale |
|---|---|---|---|---|---|
| `news_price_divergence` | `float64` | $\frac{\|r_{1d}\|}{\ln(\text{news\_count}_{1d} + 1) + 1}$ | 1 day | $[0.0, 0.30+]$ | High return in a news vacuum; flagship indicator for unannounced insider price movements. |
| `volume_news_divergence` | `float64` | $\text{volume\_zscore}_{20d} - \text{news\_velocity\_zscore}_{30d}$ | Joint | $[-5.0, +10.0+]$ | Abnormal volume unbacked by news; detects aggressive institutional accumulation or leakage before public news. |
| `sentiment_return_alignment`| `int64` | $\text{sign}(r_{1d}) \times \text{sign}(\text{sentiment}_{1d})$ | 1 day | $\{-1, 0, 1\}$ | $+1$ = coherent move; $-1$ = inverted reaction (negative news + price pump); $0$ = neutral. |
| `is_unbacked_market_move` | `int64` | $\mathbf{1}_{(\|r_{1d}\| > 0.03 \lor \text{Vol}_Z > 2.5) \land \text{news\_count} = 0 \land \text{disclosure\_count} = 0}$ | 1 day | $\{0, 1\}$ | Hard trigger for unbacked abnormal price/volume shocks in complete disclosure vacuums. |

---

## 3. Storage & Schema Specifications
- **Format**: Partitioned Snappy-compressed Apache Parquet (`data/features/multimodal/year=YYYY/month=MM/`).
- **Composite Primary Key**: `(symbol: VARCHAR, trade_date: DATE)`.
- **Chronological Ordering**: Ascending strictly by `trade_date`.
