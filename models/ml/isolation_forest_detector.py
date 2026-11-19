"""
Machine Learning Anomaly Detection Engine (Phase 6 — Step 6.2)
Market Sentinel AI — Quantitative Surveillance Models

Implements unsupervised Isolation Forest ensemble for multidimensional market surveillance:
- Isolates complex non-linear combinations across returns, volatility, volume, and news divergence.
- Normalizes raw isolation path lengths to an intuitive anomaly score in [0.0, 1.0].
- Generates heuristic feature attribution explaining the principal driver of each anomaly.
- Optimized for low-memory CPU execution (16 GB RAM environment).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

logger = logging.getLogger("market_sentinel.models.ml.isolation_forest")
logger.setLevel(logging.INFO)


class IsolationForestAnomalyDetector:
    """
    Multidimensional unsupervised anomaly detector based on Isolation Forests.
    """

    DEFAULT_FEATURES = [
        "log_return_1d",
        "volatility_20d",
        "parkinson_volatility_20d",
        "volume_zscore_20d",
        "delivery_ratio",
        "news_price_divergence",
        "volume_news_divergence",
    ]

    def __init__(
        self,
        features: Optional[List[str]] = None,
        n_estimators: int = 100,
        contamination: float = 0.02,
        random_state: int = 42,
    ):
        self.features = features or self.DEFAULT_FEATURES
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state

        self.scaler = RobustScaler()
        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=-1,  # Utilize CPU cores cleanly
        )
        self.feature_medians: Dict[str, float] = {}
        self.is_fitted = False

    def _prepare_feature_matrix(self, df: pd.DataFrame, fit_mode: bool = False) -> np.ndarray:
        """
        Extracts and imputes surveillance features.
        """
        df_sub = df.copy()

        for col in self.features:
            if col not in df_sub.columns:
                df_sub[col] = 0.0

            if fit_mode:
                med = float(df_sub[col].dropna().median()) if not df_sub[col].dropna().empty else 0.0
                self.feature_medians[col] = med
                df_sub[col] = df_sub[col].fillna(med)
            else:
                med = self.feature_medians.get(col, 0.0)
                df_sub[col] = df_sub[col].fillna(med)

        X = df_sub[self.features].values
        # Ensure finite values
        X = np.nan_to_num(X, nan=0.0, posinf=1.0, neginf=-1.0)
        return X

    def fit(self, df: pd.DataFrame) -> IsolationForestAnomalyDetector:
        """
        Fits the RobustScaler and IsolationForest on historical feature records.
        """
        if df.empty or len(df) < 10:
            logger.warning("Insufficient records to fit Isolation Forest. Minimum 10 rows required.")
            return self

        X = self._prepare_feature_matrix(df, fit_mode=True)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True
        logger.info("Successfully trained IsolationForest on %d records with %d features.", len(df), len(self.features))
        return self

    def predict_anomalies(
        self, df: pd.DataFrame, quantile_threshold: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Scores records and identifies multidimensional anomalies and feature attributions.
        Supports both fixed-contamination flags and dynamic continuous quantile thresholding (Issue 23).
        """
        if df.empty:
            return pd.DataFrame()

        if not self.is_fitted:
            raise RuntimeError("Model is not fitted. Call fit() before predict_anomalies().")

        res = df.copy()
        X = self._prepare_feature_matrix(res, fit_mode=False)
        X_scaled = self.scaler.transform(X)

        # Raw decision function: lower means more anomalous (negative for anomalies)
        raw_scores = self.model.decision_function(X_scaled)

        # Normalize score into [0.0, 1.0] where 1.0 = most isolated anomaly
        # Using calibrated sigmoid transformation: 1.0 / (1.0 + exp(5.0 * raw_score))
        iforest_anomaly_score = 1.0 / (1.0 + np.exp(5.0 * raw_scores))
        res["iforest_score"] = np.round(iforest_anomaly_score, 4)

        if quantile_threshold is not None and 0.0 < quantile_threshold < 1.0:
            # Dynamic quantile thresholding calibrated against empirical distribution
            dynamic_cutoff = float(np.quantile(iforest_anomaly_score, quantile_threshold))
            res["is_iforest_anomaly"] = (iforest_anomaly_score >= dynamic_cutoff).astype(int)
        else:
            # Scikit-learn binary flag: -1 for anomaly, +1 for inlier
            raw_preds = self.model.predict(X_scaled)
            res["is_iforest_anomaly"] = (raw_preds == -1).astype(int)

        # Feature Attribution: Find feature with the largest absolute scaled deviation
        top_features = []
        for row_scaled in X_scaled:
            max_idx = int(np.argmax(np.abs(row_scaled)))
            top_features.append(self.features[max_idx])

        res["top_contributing_feature"] = top_features
        return res
