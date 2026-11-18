"""
Unit Tests for Isolation Forest Machine Learning Anomaly Detection
Market Sentinel AI — Phase 6: Step 6.2
"""

from datetime import date, timedelta
import numpy as np
import pandas as pd
import pytest

from models.ml.isolation_forest_detector import IsolationForestAnomalyDetector


@pytest.fixture
def sample_training_data():
    """Generates 100 days of typical feature records with 2 injected multidimensional anomalies."""
    np.random.seed(42)
    dates = [date(2026, 1, 1) + timedelta(days=i) for i in range(100)]
    records = []

    for i, dt in enumerate(dates):
        if i == 50:
            # Extreme anomaly: +6% return, 5.0 volume z-score, 10% delivery ratio, high divergence
            ret = 0.06
            vol_z = 5.0
            deliv = 0.10
            news_div = 0.06
            vol_news_div = 4.5
        elif i == 80:
            # Subtle multidimensional anomaly: +2.2% return, 2.8 volume z, 15% delivery, 2.5 vol news div
            ret = 0.022
            vol_z = 2.8
            deliv = 0.15
            news_div = 0.02
            vol_news_div = 2.5
        else:
            # Normal market noise
            ret = float(np.random.normal(0.0005, 0.01))
            vol_z = float(np.random.normal(0.0, 0.8))
            deliv = float(np.random.uniform(0.40, 0.65))
            news_div = abs(ret) / 1.0
            vol_news_div = vol_z - 0.1

        records.append({
            "symbol": "RELIANCE",
            "trade_date": dt,
            "log_return_1d": ret,
            "volatility_20d": 0.18,
            "parkinson_volatility_20d": 0.16,
            "volume_zscore_20d": vol_z,
            "delivery_ratio": deliv,
            "news_price_divergence": news_div,
            "volume_news_divergence": vol_news_div,
        })

    return pd.DataFrame(records)


def test_isolation_forest_initialization():
    detector = IsolationForestAnomalyDetector(n_estimators=50, contamination=0.03)
    assert detector.n_estimators == 50
    assert detector.contamination == 0.03
    assert detector.is_fitted is False


def test_isolation_forest_fit_and_predict(sample_training_data):
    detector = IsolationForestAnomalyDetector(contamination=0.03, random_state=42)
    detector.fit(sample_training_data)
    assert detector.is_fitted is True

    scored_df = detector.predict_anomalies(sample_training_data)

    assert len(scored_df) == 100
    assert "iforest_score" in scored_df.columns
    assert "is_iforest_anomaly" in scored_df.columns
    assert "top_contributing_feature" in scored_df.columns

    # Verify scores are bounded strictly in [0.0, 1.0]
    scores = scored_df["iforest_score"]
    assert ((scores >= 0.0) & (scores <= 1.0)).all()

    # The injected extreme anomaly on Day 50 must be detected
    row_day50 = scored_df.iloc[50]
    assert row_day50["is_iforest_anomaly"] == 1
    assert row_day50["iforest_score"] > 0.60
    assert row_day50["top_contributing_feature"] in [
        "log_return_1d",
        "volume_zscore_20d",
        "news_price_divergence",
        "volume_news_divergence",
    ]


def test_isolation_forest_predict_before_fit_raises_error(sample_training_data):
    detector = IsolationForestAnomalyDetector()
    with pytest.raises(RuntimeError, match="Model is not fitted"):
        detector.predict_anomalies(sample_training_data)


def test_isolation_forest_empty_dataframe():
    detector = IsolationForestAnomalyDetector()
    # Fit with empty should not crash
    assert detector.fit(pd.DataFrame()).is_fitted is False
    # Predict with empty should return empty
    detector.is_fitted = True
    assert detector.predict_anomalies(pd.DataFrame()).empty
