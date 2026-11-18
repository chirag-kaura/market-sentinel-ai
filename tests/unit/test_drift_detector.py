"""
Unit tests for Statistical Data & Prediction Drift Monitoring (Phase 11 — Step 11.4).
"""

import numpy as np
import pandas as pd
import pytest
from monitoring.drift.drift_detector import DriftDetector


def test_psi_identical_distributions():
    detector = DriftDetector()
    data = np.random.normal(loc=0.0, scale=1.0, size=500)
    psi = detector.calculate_psi(data, data)
    assert psi < 0.05  # Virtually zero for identical samples


def test_drift_detection_stationary_features():
    detector = DriftDetector()
    np.random.seed(42)
    ref = np.random.normal(loc=10.0, scale=2.0, size=400)
    cur = np.random.normal(loc=10.05, scale=2.02, size=400)

    res = detector.analyze_feature_drift("volume_ratio", ref.tolist(), cur.tolist())
    assert not res.is_drifted
    assert res.drift_level == "NONE"


def test_drift_detection_regime_shift():
    detector = DriftDetector()
    np.random.seed(42)
    # Baseline normal market volatility
    ref = np.random.normal(loc=0.0, scale=1.0, size=500)
    # Severe market shock regime shift
    cur = np.random.normal(loc=2.5, scale=3.5, size=500)

    res = detector.analyze_feature_drift("abnormal_return", ref.tolist(), cur.tolist())
    assert res.is_drifted
    assert res.drift_level == "CRITICAL"
    assert res.psi_score > 0.25


def test_multivariate_drift_audit():
    detector = DriftDetector()
    np.random.seed(42)
    ref_df = pd.DataFrame({
        "abnormal_return": np.random.normal(0, 1, 300),
        "volume_ratio": np.random.exponential(1.5, 300),
    })
    cur_df = pd.DataFrame({
        "abnormal_return": np.random.normal(0, 1, 300),
        "volume_ratio": np.random.exponential(5.0, 300),  # Heavy shift
    })

    report = detector.run_drift_audit(ref_df, cur_df, ["abnormal_return", "volume_ratio"])
    assert report.overall_drift_detected
    assert not report.metrics["abnormal_return"].is_drifted
    assert report.metrics["volume_ratio"].is_drifted
