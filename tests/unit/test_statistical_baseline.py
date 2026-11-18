"""
Unit Tests for Statistical Baseline Anomaly Detection Engine
Market Sentinel AI — Phase 6: Step 6.1
"""

from datetime import date, timedelta
import numpy as np
import pandas as pd
import pytest

from models.statistical.baseline_detector import AnomalyThresholdConfig, StatisticalBaselineDetector


@pytest.fixture
def sample_surveillance_df():
    """Generates 30 days of market and cross-modal features with known anomalies."""
    dates = [date(2026, 3, 1) + timedelta(days=i) for i in range(30)]
    records = []
    for i, dt in enumerate(dates):
        # Day 10 is an extreme ALERT anomaly: 5% return, 4.0 volume Z, 15% delivery ratio, unbacked
        if i == 10:
            ret = 0.05
            vol_z = 4.2
            deliv_ratio = 0.15
            unbacked = 1
        # Day 20 is a moderate SUSPICIOUS anomaly: 2.5% return, 2.5 volume Z
        elif i == 20:
            ret = 0.025
            vol_z = 2.5
            deliv_ratio = 0.45
            unbacked = 0
        else:
            ret = 0.003
            vol_z = 0.2
            deliv_ratio = 0.55
            unbacked = 0

        records.append({
            "symbol": "RELIANCE",
            "trade_date": dt,
            "log_return_1d": ret,
            "volatility_20d": 0.20,
            "volume_zscore_20d": vol_z,
            "delivery_ratio": deliv_ratio,
            "news_price_divergence": ret / 1.0,
            "is_unbacked_market_move": unbacked,
        })
    return pd.DataFrame(records)


def test_detector_initialization_and_fit(sample_surveillance_df):
    detector = StatisticalBaselineDetector()
    assert detector.is_fitted is False

    detector.fit(sample_surveillance_df)
    assert detector.is_fitted is True
    assert "log_return_1d" in detector.empirical_percentiles
    assert "volume_zscore_20d" in detector.empirical_percentiles
    assert detector.empirical_percentiles["log_return_1d"]["p99"] > 0.0


def test_detect_anomalies_scoring_and_tiering(sample_surveillance_df):
    detector = StatisticalBaselineDetector()
    detector.fit(sample_surveillance_df)
    results = detector.detect_anomalies(sample_surveillance_df)

    assert len(results) == 30
    assert "statistical_anomaly_score" in results.columns
    assert "severity_tier" in results.columns
    assert "delivery_divergence_flag" in results.columns

    # Verify Day 10 is classified as ALERT
    row_day10 = results.iloc[10]
    assert row_day10["severity_tier"] == "ALERT"
    assert row_day10["statistical_anomaly_score"] >= 0.70
    assert row_day10["delivery_divergence_flag"] == 1
    assert row_day10["return_zscore"] > 3.0

    # Verify Day 20 is classified as WATCHLIST or SUSPICIOUS
    row_day20 = results.iloc[20]
    assert row_day20["severity_tier"] in ["WATCHLIST", "SUSPICIOUS"]
    assert row_day20["delivery_divergence_flag"] == 0

    # Verify normal days are classified as NORMAL
    row_day0 = results.iloc[0]
    assert row_day0["severity_tier"] == "NORMAL"
    assert row_day0["statistical_anomaly_score"] < 0.25


def test_detect_anomalies_bounds_and_empty():
    detector = StatisticalBaselineDetector()
    assert detector.detect_anomalies(pd.DataFrame()).empty

    # Verify scores are bounded strictly in [0.0, 1.0]
    df_extreme = pd.DataFrame([{
        "symbol": "INFY",
        "trade_date": date(2026, 3, 30),
        "log_return_1d": 0.50,
        "volatility_20d": 0.10,
        "volume_zscore_20d": 15.0,
        "delivery_ratio": 0.05,
        "is_unbacked_market_move": 1,
    }])
    res_extreme = detector.detect_anomalies(df_extreme)
    score = res_extreme["statistical_anomaly_score"].iloc[0]
    assert 0.0 <= score <= 1.0
