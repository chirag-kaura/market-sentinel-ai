"""
Benchmark Scenario Parity Tests: Statistical vs Machine Learning vs Volatility Models
Market Sentinel AI — Phase 6: Step 6.5
"""

from datetime import date, timedelta
import numpy as np
import pandas as pd
import pytest

from models.ml.isolation_forest_detector import IsolationForestAnomalyDetector
from models.statistical.baseline_detector import StatisticalBaselineDetector
from models.statistical.volatility_models import (
    DynamicVolatilityBandGenerator,
    EWMAVolatilityForecaster,
)


@pytest.fixture
def benchmark_scenario_dataset():
    """
    Generates 60 days of market data with two distinct injected anomalies:
    - Day 30: Blatant 3-sigma single-metric return shock (+5.5%).
    - Day 50: Subtle multidimensional insider accumulation (+1.8% return, +2.2 vol Z, 12% delivery, zero news).
    """
    np.random.seed(42)
    dates = [date(2026, 1, 1) + timedelta(days=i) for i in range(60)]
    records = []
    base_price = 1000.0

    for i, dt in enumerate(dates):
        if i == 30:
            ret = 0.055
            vol_z = 3.5
            deliv = 0.55
            news_div = 0.055
            vol_news_div = 3.5
        elif i == 50:
            # Subtle multidimensional anomaly
            ret = 0.018
            vol_z = 2.2
            deliv = 0.12
            news_div = 0.018
            vol_news_div = 2.2
        else:
            ret = float(np.random.normal(0.0005, 0.01))
            vol_z = float(np.random.normal(0.0, 0.6))
            deliv = float(np.random.uniform(0.45, 0.60))
            news_div = abs(ret) / 1.0
            vol_news_div = vol_z

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
            "is_unbacked_market_move": 1 if i == 50 else 0,
        })

    return pd.DataFrame(records)


def test_scenario_a_blatant_shock_caught_by_both(benchmark_scenario_dataset):
    """
    Scenario A: Day 30 has a blatant +5.5% return shock.
    Both Statistical Baseline and Isolation Forest should catch this anomaly.
    """
    # 1. Statistical Baseline
    stat_detector = StatisticalBaselineDetector()
    stat_detector.fit(benchmark_scenario_dataset)
    stat_res = stat_detector.detect_anomalies(benchmark_scenario_dataset)

    row_day30_stat = stat_res.iloc[30]
    assert row_day30_stat["severity_tier"] in ["ALERT", "SUSPICIOUS"]
    assert row_day30_stat["return_zscore"] > 3.0

    # 2. Isolation Forest
    ml_detector = IsolationForestAnomalyDetector(contamination=0.05, random_state=42)
    ml_detector.fit(benchmark_scenario_dataset)
    ml_res = ml_detector.predict_anomalies(benchmark_scenario_dataset)

    row_day30_ml = ml_res.iloc[30]
    assert row_day30_ml["is_iforest_anomaly"] == 1
    assert row_day30_ml["iforest_score"] > 0.60


def test_scenario_b_subtle_multidimensional_leak_caught_by_ml(benchmark_scenario_dataset):
    """
    Scenario B: Day 50 has a subtle multi-dimensional anomaly (+1.8% return, +2.2 vol Z, 12% delivery).
    Neither return Z nor vol Z exceeds the critical 3.0 threshold.
    Statistical baseline does NOT trigger ALERT, but Isolation Forest DOES catch it.
    """
    stat_detector = StatisticalBaselineDetector()
    stat_detector.fit(benchmark_scenario_dataset)
    stat_res = stat_detector.detect_anomalies(benchmark_scenario_dataset)

    row_day50_stat = stat_res.iloc[50]
    # Statistical baseline misses the critical ALERT threshold
    assert row_day50_stat["severity_tier"] != "ALERT"
    assert row_day50_stat["return_zscore"] < 3.0

    ml_detector = IsolationForestAnomalyDetector(contamination=0.05, random_state=42)
    ml_detector.fit(benchmark_scenario_dataset)
    ml_res = ml_detector.predict_anomalies(benchmark_scenario_dataset)

    row_day50_ml = ml_res.iloc[50]
    # Isolation Forest isolates the multi-dimensional outlier
    assert row_day50_ml["is_iforest_anomaly"] == 1
    assert row_day50_ml["iforest_score"] > 0.55


def test_scenario_c_dynamic_volatility_envelope_expansion(benchmark_scenario_dataset):
    """
    Scenario C: Verifies that EWMA volatility expands bands in response to shocks,
    preventing subsequent moderate price volatility from false alarming.
    """
    forecaster = EWMAVolatilityForecaster(decay_factor=0.94)
    cond_vol = forecaster.compute_conditional_volatility(benchmark_scenario_dataset["log_return_1d"])

    bands = DynamicVolatilityBandGenerator.generate_bands(
        prices=benchmark_scenario_dataset["close_price"],
        conditional_volatility=cond_vol,
        num_std=3.0,
    )

    # Post-shock (day 31-35), upper band distance from price must be wider than pre-shock (day 20)
    band_width_day20 = bands["dynamic_upper_band"].iloc[20] - bands["dynamic_lower_band"].iloc[20]
    band_width_day32 = bands["dynamic_upper_band"].iloc[32] - bands["dynamic_lower_band"].iloc[32]

    assert band_width_day32 > band_width_day20
