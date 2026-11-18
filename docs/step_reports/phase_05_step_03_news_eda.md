# Step Report: Phase 5 — Step 5.3: News & Corporate Disclosures EDA

**Document ID**: `docs/step_reports/phase_05_step_03_news_eda.md`  
**Phase**: Phase 5 — Financial Feature Engineering & Exploratory Data Analysis (EDA)  
**Step**: Step 5.3 — News & Corporate Disclosures EDA (`processing/eda/news_eda.py`)  
**Status**: APPROVED / COMPLETED  
**Date**: 2026-11-17  

---

## 1. Objective & Business Relevance
- **Objective**: Implement the unstructured text and corporate disclosure exploratory data analysis module (`processing/eda/news_eda.py`) to profile financial media articles and regulatory filings across our 15 constituent equities, evaluating publication timing distributions (market hours vs post-market vs weekend), coverage skew across bellwethers and smaller constituents, announcement classification frequencies, and inter-arrival burstiness.
- **Business Relevance**: Surveillance platforms detect insider trading by correlating abnormal price movements with material non-public information (MNPI) leaks before disclosures are made public. Establishing the baseline publication rhythm, coverage distributions, and inter-arrival patterns of news prevents false positives during scheduled earnings seasons and provides the statistical basis for symbol-level news intensity feature engineering (Step 5.4).

---

## 2. Technical Explanation & Architectural Fit
- **NewsDistributionProfile & Profiler Architecture**:
  - `is_market_hours_utc`: Flags whether an article was published during NSE active market hours (09:15 to 15:30 IST / 03:45 to 10:00 UTC) on weekdays.
  - `profile_news_corpus`: Analyzes corpus-wide symbol coverage, headline and summary word count distributions, weekend vs weekday percentages, and computes mean, median, and 95th percentile inter-arrival deltas.
  - `profile_corporate_disclosures`: Groups official regulatory filings into functional surveillance categories (Financial Results, Board Meetings, Regulatory Filings, Corporate Actions).
- **Synthesis Report**:
  - Authored [`docs/models/eda_news_report.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/models/eda_news_report.md) documenting empirical findings and translating them into concrete feature engineering directives (e.g., using symbol-relative Z-scores rather than absolute counts due to mega-cap media skew).

---

## 3. Technology Decisions & Alternatives Considered
- **Timezone Standardization**:
  - All inter-arrival calculations and market-hour checks normalize internal timestamps to UTC (`datetime.timezone.utc`), eliminating day-light savings or regional ambiguity while mapping cleanly to IST market intervals.
- **Robust Delta Percentiles**:
  - Used median and 95th percentile along with sample mean to account for extreme inter-arrival outliers (e.g. multi-day gaps over holiday weekends).

---

## 4. Files Created / Modified
- `processing/eda/news_eda.py`: News and corporate disclosure statistical EDA profiler.
- `tests/unit/test_news_eda.py`: Automated unit tests (4 test cases) verifying market hour classification, corpus statistics, corporate filing categories, and empty corpus handling.
- `docs/models/eda_news_report.md`: Formal News & Disclosure EDA Report.
- `docs/step_reports/phase_05_step_03_news_eda.md`: Step documentation and operational guidelines.
- `docs/PROJECT_TRACKER.md`: Updated Step 5.3 status to `COMPLETED`.
- `docs/CHANGELOG.md`: Logged Step 5.3 completion.

---

## 5. Commands Executed & Testing Report
- **Command**: `python -m pytest tests/unit/test_news_eda.py -v`
  - Output: `4 passed in 1.21s`
- **Command**: `python -m pytest tests/ -v`
  - Output: `50 passed in 6.55s` across all 50 repository test cases.

---

## 6. Known Limitations, Risks & Edge Cases
- **Exchange Holidays**: Fixed market hour filters evaluate Monday–Friday trading windows; exchange trading holidays (e.g., Diwali, Independence Day) are accounted for downstream when aligning with historical Bhavcopy trading calendars.

---

## 7. Status & Next Step
- **Step 5.3 Status**: COMPLETED & VERIFIED.
- **Proposed Next Step**: Proceed to **Phase 5 — Step 5.4: News Feature Engineering** (`processing/features/news_features.py` computing rolling 1d/3d/7d news intensity, symbol-relative velocity Z-scores, announcement category binary flags, and sentiment polarity proxies).
