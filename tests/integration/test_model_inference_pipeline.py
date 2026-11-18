"""
Integration Tests for Surveillance Ensemble Inference Engine
Market Sentinel AI — Phase 6: Step 6.7
"""

from datetime import date, timedelta
import numpy as np
import pandas as pd
import pytest

from models.inference.ensemble_engine import SurveillanceEnsembleEngine, SurveillanceInferenceResult


@pytest.fixture
def mock_multimodal_dataset():
    """Generates 50 days of multimodal surveillance features with an injected critical anomaly."""
    dates = [date(2026, 2, 1) + timedelta(days=i) for i in range(50)]
    records = []
    base_price = 2500.0

    for i, dt in enumerate(dates):
        if i == 40:
            # Critical anomaly: +5.8% return, 4.5 volume Z, 12% delivery, unbacked move
            ret = 0.058
            vol_z = 4.5
            deliv = 0.12
            news_div = 0.058
            vol_news_div = 4.5
            unbacked = 1
        else:
            ret = float(np.random.normal(0.0005, 0.01))
            vol_z = float(np.random.normal(0.0, 0.7))
            deliv = float(np.random.uniform(0.45, 0.60))
            news_div = abs(ret) / 1.0
            vol_news_div = vol_z
            unbacked = 0

        base_price *= np.exp(ret)
        records.append({
            "symbol": "RELIANCE",
            "trade_date": dt,
            "close_price": base_price,
            "log_return_1d": ret,
            "volatility_20d": 0.18,
            "parkinson_volatility_20d": 0.16,
            "volume_zscore_20d": vol_z,
            "delivery_ratio": deliv,
            "news_price_divergence": news_div,
            "volume_news_divergence": vol_news_div,
            "is_unbacked_market_move": unbacked,
        })

    return pd.DataFrame(records)


def test_ensemble_engine_fit_and_inference(mock_multimodal_dataset):
    engine = SurveillanceEnsembleEngine()
    engine.fit(mock_multimodal_dataset)
    assert engine.is_fitted is True

    results = engine.score_record(mock_multimodal_dataset)

    assert len(results) == 50
    assert all(isinstance(r, SurveillanceInferenceResult) for r in results)

    # 1. Verify mathematically bounded scores in [0.0, 1.0]
    for r in results:
        assert 0.0 <= r.ensemble_anomaly_score <= 1.0
        assert 0.0 <= r.baseline_score <= 1.0
        assert 0.0 <= r.iforest_score <= 1.0
        assert r.severity_tier in ["NORMAL", "WATCHLIST", "SUSPICIOUS", "CRITICAL_ALERT"]

    # 2. Verify Day 40 injected anomaly is flagged as CRITICAL_ALERT or SUSPICIOUS
    anom_result = results[40]
    assert anom_result.ensemble_anomaly_score > 0.50
    assert anom_result.is_anomaly is True
    assert anom_result.severity_tier in ["CRITICAL_ALERT", "SUSPICIOUS"]


def test_ensemble_engine_latency_performance(mock_multimodal_dataset):
    """
    Verifies that per-record inference execution latency is strictly < 10 ms on CPU.
    """
    engine = SurveillanceEnsembleEngine()
    engine.fit(mock_multimodal_dataset)

    # Run single-record scoring
    single_record = mock_multimodal_dataset.iloc[0:1].copy()
    res = engine.score_record(single_record)

    assert len(res) == 1
    # Average per-record latency across 50 records in batch
    batch_res = engine.score_record(mock_multimodal_dataset)
    avg_latency_ms = batch_res[0].execution_time_ms
    assert avg_latency_ms < 10.0, f"Inference latency too slow: {avg_latency_ms} ms per record"


def test_ensemble_engine_empty_input():
    engine = SurveillanceEnsembleEngine()
    assert engine.score_record(pd.DataFrame()) == []
