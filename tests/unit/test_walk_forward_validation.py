"""
Unit Tests for Chronological Walk-Forward Validation Engine
Market Sentinel AI — Phase 6: Step 6.4
"""

from datetime import date, timedelta
import numpy as np
import pandas as pd
import pytest

from models.ml.isolation_forest_detector import IsolationForestAnomalyDetector
from models.statistical.baseline_detector import StatisticalBaselineDetector
from models.validation.walk_forward import TimeSeriesWalkForwardValidator


@pytest.fixture
def chronological_dataset():
    """Generates 90 days of chronological feature data for 2 symbols."""
    np.random.seed(42)
    dates = [date(2026, 1, 1) + timedelta(days=i) for i in range(90)]
    records = []

    for sym in ["RELIANCE", "TCS"]:
        for i, dt in enumerate(dates):
            records.append({
                "symbol": sym,
                "trade_date": dt,
                "log_return_1d": float(np.random.normal(0.0005, 0.015)),
                "volatility_20d": 0.18,
                "parkinson_volatility_20d": 0.16,
                "volume_zscore_20d": float(np.random.normal(0.0, 1.0)),
                "delivery_ratio": float(np.random.uniform(0.40, 0.60)),
                "news_price_divergence": 0.01,
                "volume_news_divergence": 0.0,
                "is_unbacked_market_move": 0,
            })

    return pd.DataFrame(records)


def test_walk_forward_strict_chronological_ordering_and_embargo(chronological_dataset):
    validator = TimeSeriesWalkForwardValidator(
        n_splits=3,
        min_train_days=30,
        test_days=15,
        embargo_days=2,
        expanding=True,
    )

    splits = list(validator.split(chronological_dataset))
    assert len(splits) == 3

    for fold_idx, (train_fold, test_fold) in enumerate(splits):
        assert not train_fold.empty
        assert not test_fold.empty

        max_train_date = train_fold["trade_date"].max()
        min_test_date = test_fold["trade_date"].min()

        # Strict temporal inequality: train_date + embargo <= test_date
        assert (min_test_date - max_train_date).days >= 3  # 2 days embargo + 1 day step
        assert max_train_date < min_test_date

        # Zero row overlap
        train_indices = set(train_fold.index)
        test_indices = set(test_fold.index)
        assert len(train_indices.intersection(test_indices)) == 0


def test_walk_forward_expanding_vs_rolling(chronological_dataset):
    validator_exp = TimeSeriesWalkForwardValidator(n_splits=3, min_train_days=25, test_days=10, expanding=True)
    splits_exp = list(validator_exp.split(chronological_dataset))

    validator_roll = TimeSeriesWalkForwardValidator(n_splits=3, min_train_days=25, test_days=10, expanding=False)
    splits_roll = list(validator_roll.split(chronological_dataset))

    # Expanding window: train rows must increase monotonically with each fold
    assert len(splits_exp[0][0]) < len(splits_exp[1][0]) < len(splits_exp[2][0])

    # Rolling window: train rows remain constant size (approx min_train_days * 2 symbols)
    assert abs(len(splits_roll[0][0]) - len(splits_roll[1][0])) <= 4


def test_walk_forward_evaluate_isolation_forest(chronological_dataset):
    validator = TimeSeriesWalkForwardValidator(
        n_splits=2,
        min_train_days=35,
        test_days=15,
        embargo_days=2,
    )

    fold_metrics = validator.evaluate_detector(
        detector_factory=lambda: IsolationForestAnomalyDetector(n_estimators=30, contamination=0.03),
        df=chronological_dataset,
        score_col="iforest_score",
        flag_col="is_iforest_anomaly",
    )

    assert len(fold_metrics) == 2
    for m in fold_metrics:
        assert m.train_rows > 0
        assert m.test_rows > 0
        assert 0.0 <= m.test_anomaly_rate <= 1.0
        assert 0.0 <= m.mean_anomaly_score <= 1.0


def test_walk_forward_evaluate_statistical_baseline(chronological_dataset):
    validator = TimeSeriesWalkForwardValidator(
        n_splits=2,
        min_train_days=35,
        test_days=15,
        embargo_days=2,
    )

    fold_metrics = validator.evaluate_detector(
        detector_factory=lambda: StatisticalBaselineDetector(),
        df=chronological_dataset,
        score_col="statistical_anomaly_score",
        flag_col="return_p99_flag",
    )

    assert len(fold_metrics) == 2
    for m in fold_metrics:
        assert m.train_rows > 0
        assert m.test_rows > 0
        assert 0.0 <= m.mean_anomaly_score <= 1.0


def test_walk_forward_empty_or_short_dataset():
    validator = TimeSeriesWalkForwardValidator(n_splits=3, min_train_days=30)
    assert list(validator.split(pd.DataFrame())) == []

    # Dataset with only 5 days cannot satisfy 30-day train
    short_df = pd.DataFrame({
        "trade_date": [date(2026, 1, 1) + timedelta(days=i) for i in range(5)],
        "close_price": [100, 101, 102, 103, 104],
    })
    assert list(validator.split(short_df)) == []
