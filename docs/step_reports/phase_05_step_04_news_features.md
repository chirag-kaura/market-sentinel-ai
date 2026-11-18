# Step Report: Phase 5 — Step 5.4: News Feature Engineering

**Document ID**: `docs/step_reports/phase_05_step_04_news_features.md`  
**Phase**: Phase 5 — Financial Feature Engineering & Exploratory Data Analysis (EDA)  
**Step**: Step 5.4 — News Feature Engineering (`processing/features/news_features.py`)  
**Status**: APPROVED / COMPLETED  
**Date**: 2026-11-17  

---

## 1. Objective & Business Relevance
- **Objective**: Implement the structured news and corporate disclosure feature extraction pipeline (`processing/features/news_features.py`) to convert unstructured articles and regulatory filings into daily time-series features aligned by (symbol, trade_date):
  - Daily, 3-day, and 7-day cumulative news arrival counts.
  - 30-day baseline symbol-relative news velocity Z-scores (`news_velocity_zscore_30d`).
  - Binary surveillance flags for high-impact disclosure types (`has_financial_results`, `has_board_meeting`, `has_mna_filing`, `has_compliance_action`).
  - Lexicon-based sentiment polarity proxy (`avg_sentiment_polarity_1d` in $[-1.0, +1.0]$).
  - Strict post-market date rollover attributing post-15:30 IST releases to the next trade day to eliminate look-ahead leakage.
- **Business Relevance**: Insider trading and front-running surveillance relies on identifying unannounced price movements prior to official disclosures. Transforming text streams into standardized numerical features allows the anomaly detection engine to detect volume/volatility anomalies that occur in complete news vacuums versus volume surges justified by earnings announcements.

---

## 2. Technical Explanation & Architectural Fit
- **Causal Trade Date Mapping (`attribute_to_trading_date`)**:
  - Articles published before 10:00 UTC (15:30 IST) are attributed to trade date $d$.
  - Disclosures filed after 10:00 UTC are attributed to $d+1$, matching the exact market session in which participants could react.
- **Symbol-Relative Velocity Normalization**:
  - Normalized by 30-day rolling baseline:
    $$Z_{\text{news}} = \frac{\text{Count}_{1d} - \mu_{30}}{\sigma_{30} + \epsilon}$$
    This normalizes for the structural media skew between mega-caps and less covered constituents identified in Step 5.3.
- **Sentiment Polarity Scoring**:
  - Evaluates headline and summary tokens against domain-specific financial sentiment lexicons (Loughran-McDonald inspired), bounding polarity strictly to $[-1.0, +1.0]$.

---

## 3. Technology Decisions & Alternatives Considered
- **Lexicon-Based Sentiment in Phase 5 vs Transformer Embeddings**:
  - Lexicon heuristics provide ultra-fast ($< 1\text{ ms}$ per article), zero-GPU daily feature computation. Deep transformer-based sentiment and NER are decoupled into Phase 7 (NLP & News Intelligence) and Phase 9 (Grounded RAG).
- **Post-Market Rollover vs Trade-Date Clamping**:
  - Attributing post-market filings to the subsequent session strictly enforces causal timeline consistency and prevents look-ahead bias during historical model training.

---

## 4. Files Created / Modified
- `processing/features/news_features.py`: News and corporate disclosure feature extraction engine (`NewsFeatureExtractor`).
- `tests/unit/test_news_features.py`: Automated unit tests (4 test cases) validating post-market rollover, lexicon polarity, daily feature extraction, and empty handling.
- `docs/step_reports/phase_05_step_04_news_features.md`: Step documentation and operational guidelines.
- `docs/PROJECT_TRACKER.md`: Updated Step 5.4 status to `COMPLETED`.
- `docs/CHANGELOG.md`: Logged Step 5.4 completion.

---

## 5. Commands Executed & Testing Report
- **Command**: `python -m pytest tests/unit/test_news_features.py -v`
  - Output: `4 passed in 1.25s`
- **Command**: `python -m pytest tests/ -v`
  - Output: `54 passed in 6.89s` across all 54 repository test cases.

---

## 6. Known Limitations, Risks & Edge Cases
- **Lexicon Ambiguity**: Lexicon polarity does not capture complex negations (e.g. "not a loss"); this is intentionally treated as a fast feature baseline, with deep semantic contextual analysis reserved for Phase 7 / Phase 9.

---

## 7. Status & Next Step
- **Step 5.4 Status**: COMPLETED & VERIFIED.
- **Proposed Next Step**: Proceed to **Phase 5 — Step 5.5: Multimodal Market-News Feature Alignment** (`processing/features/multimodal_alignment.py` performing outer/left joins of market and news features, forward-filling, and creating cross-modal interaction indicators).
