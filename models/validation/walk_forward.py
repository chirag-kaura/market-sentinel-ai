"""
Chronological Walk-Forward Validation Engine (Phase 6 — Step 6.4)
Market Sentinel AI — Time-Series Model Validation

Enforces strictly causal financial cross-validation:
- Expanding-window and rolling-window chronological splits.
- Purging and embargo buffers between training and out-of-sample testing sets.
- Out-of-sample anomaly stability and detector performance evaluation.
- Strictly forbids random K-Fold splits to eliminate look-ahead leakage.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger("market_sentinel.models.validation.walk_forward")
logger.setLevel(logging.INFO)


@dataclass
class FoldMetrics:
    fold_idx: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    train_rows: int
    test_rows: int
    test_anomaly_rate: float
    mean_anomaly_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fold_idx": self.fold_idx,
            "train_start": self.train_start,
            "train_end": self.train_end,
            "test_start": self.test_start,
            "test_end": self.test_end,
            "train_rows": self.train_rows,
            "test_rows": self.test_rows,
            "test_anomaly_rate": round(self.test_anomaly_rate, 4),
            "mean_anomaly_score": round(self.mean_anomaly_score, 4),
        }


class TimeSeriesWalkForwardValidator:
    """
    Splits chronological market time series into walk-forward train and test folds.
    Enforces purging and embargo intervals to eliminate autoregressive leakage.
    """

    def __init__(
        self,
        n_splits: int = 4,
        min_train_days: int = 30,
        test_days: int = 15,
        embargo_days: int = 2,
        expanding: bool = True,
    ):
        self.n_splits = n_splits
        self.min_train_days = min_train_days
        self.test_days = test_days
        self.embargo_days = embargo_days
        self.expanding = expanding

    def split(
        self,
        df: pd.DataFrame,
        date_col: str = "trade_date",
    ) -> Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]:
        """
        Yields chronological (train_df, test_df) tuples partitioned by unique dates.
        """
        if df.empty or date_col not in df.columns:
            return

        # Ensure date sorting
        df_sorted = df.copy()
        df_sorted[date_col] = pd.to_datetime(df_sorted[date_col]).dt.date
        unique_dates = sorted(df_sorted[date_col].unique())
        total_dates = len(unique_dates)

        # Required minimum span: min_train + embargo + test
        min_required = self.min_train_days + self.embargo_days + self.test_days
        if total_dates < min_required:
            logger.warning(
                "Total unique dates (%d) is less than required minimum (%d). Cannot generate splits.",
                total_dates,
                min_required,
            )
            return

        # Calculate stride between successive test folds
        remaining_dates = total_dates - min_required
        stride = max(1, remaining_dates // max(1, self.n_splits - 1)) if self.n_splits > 1 else remaining_dates

        splits_generated = 0
        for i in range(self.n_splits):
            train_end_idx = self.min_train_days + (i * stride)
            test_start_idx = train_end_idx + self.embargo_days
            test_end_idx = test_start_idx + self.test_days

            if test_end_idx > total_dates:
                # Truncate test window to dataset end if past bound
                test_end_idx = total_dates
                if test_start_idx >= test_end_idx:
                    break

            if self.expanding:
                train_dates = set(unique_dates[0:train_end_idx])
            else:
                train_start_idx = max(0, train_end_idx - self.min_train_days)
                train_dates = set(unique_dates[train_start_idx:train_end_idx])

            test_dates = set(unique_dates[test_start_idx:test_end_idx])

            train_fold = df_sorted[df_sorted[date_col].isin(train_dates)].copy()
            test_fold = df_sorted[df_sorted[date_col].isin(test_dates)].copy()

            splits_generated += 1
            yield train_fold, test_fold

            if test_end_idx == total_dates:
                break

    def evaluate_detector(
        self,
        detector_factory: Callable[[], Any],
        df: pd.DataFrame,
        score_col: str = "iforest_score",
        flag_col: str = "is_iforest_anomaly",
        date_col: str = "trade_date",
    ) -> List[FoldMetrics]:
        """
        Executes chronological walk-forward cross-validation on an anomaly detector.
        """
        fold_results: List[FoldMetrics] = []

        for idx, (train_df, test_df) in enumerate(self.split(df, date_col=date_col)):
            # Instantiate fresh detector per fold to ensure clean isolation
            detector = detector_factory()
            detector.fit(train_df)

            # Predict on out-of-sample test fold
            if hasattr(detector, "predict_anomalies"):
                scored_test = detector.predict_anomalies(test_df)
            elif hasattr(detector, "detect_anomalies"):
                scored_test = detector.detect_anomalies(test_df)
            else:
                raise AttributeError("Detector must implement predict_anomalies or detect_anomalies.")

            anomaly_rate = float(scored_test[flag_col].mean()) if flag_col in scored_test.columns else 0.0
            mean_score = float(scored_test[score_col].mean()) if score_col in scored_test.columns else 0.0

            fold_results.append(
                FoldMetrics(
                    fold_idx=idx + 1,
                    train_start=str(train_df[date_col].min()),
                    train_end=str(train_df[date_col].max()),
                    test_start=str(test_df[date_col].min()),
                    test_end=str(test_df[date_col].max()),
                    train_rows=len(train_df),
                    test_rows=len(test_df),
                    test_anomaly_rate=anomaly_rate,
                    mean_anomaly_score=mean_score,
                )
            )

        return fold_results
