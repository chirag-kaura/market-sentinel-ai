"""
Surveillance Ensemble Inference Engine (Phase 6 — Step 6.7)
Market Sentinel AI — Production Model Inference Pipeline

Unifies the 3 quantitative surveillance model families into a high-performance,
explainable ensemble scoring engine:
1. Statistical Baseline Detector (linear Z-scores & delivery divergence).
2. Machine Learning Isolation Forest (multidimensional non-linear outlier isolation).
3. Dynamic Volatility Envelopes (regime-adaptive price bands).

Formula:
Final Score = 0.40 * Score_Baseline + 0.40 * Score_IForest + 0.20 * Vol_Band_Breach
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from models.ml.isolation_forest_detector import IsolationForestAnomalyDetector
from models.statistical.baseline_detector import StatisticalBaselineDetector
from models.statistical.volatility_models import (
    DynamicVolatilityBandGenerator,
    EWMAVolatilityForecaster,
)

logger = logging.getLogger("market_sentinel.models.inference.ensemble")
logger.setLevel(logging.INFO)


@dataclass
class SurveillanceInferenceResult:
    symbol: str
    trade_date: str
    ensemble_anomaly_score: float
    severity_tier: str
    is_anomaly: bool
    baseline_score: float
    iforest_score: float
    is_volatility_band_breach: bool
    top_contributing_feature: str
    execution_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "trade_date": self.trade_date,
            "ensemble_anomaly_score": round(self.ensemble_anomaly_score, 4),
            "severity_tier": self.severity_tier,
            "is_anomaly": self.is_anomaly,
            "baseline_score": round(self.baseline_score, 4),
            "iforest_score": round(self.iforest_score, 4),
            "is_volatility_band_breach": self.is_volatility_band_breach,
            "top_contributing_feature": self.top_contributing_feature,
            "execution_time_ms": round(self.execution_time_ms, 2),
        }


class SurveillanceEnsembleEngine:
    """
    Production-ready model inference engine evaluating multimodal surveillance records.
    """

    def __init__(
        self,
        baseline_detector: Optional[StatisticalBaselineDetector] = None,
        iforest_detector: Optional[IsolationForestAnomalyDetector] = None,
        volatility_forecaster: Optional[EWMAVolatilityForecaster] = None,
        weight_baseline: float = 0.40,
        weight_iforest: float = 0.40,
        weight_volatility: float = 0.20,
    ):
        self.baseline_detector = baseline_detector or StatisticalBaselineDetector()
        self.iforest_detector = iforest_detector or IsolationForestAnomalyDetector(contamination=0.03)
        self.volatility_forecaster = volatility_forecaster or EWMAVolatilityForecaster(decay_factor=0.94)

        self.weight_baseline = weight_baseline
        self.weight_iforest = weight_iforest
        self.weight_volatility = weight_volatility
        self.is_fitted = False

    def fit(self, historical_df: pd.DataFrame) -> SurveillanceEnsembleEngine:
        """
        Fits all constituent sub-models on historical surveillance feature data.
        """
        if historical_df.empty or len(historical_df) < 10:
            logger.warning("Insufficient data to fit ensemble engine. Minimum 10 rows required.")
            return self

        # 1. Fit statistical baseline percentiles
        self.baseline_detector.fit(historical_df)

        # 2. Fit Isolation Forest ensemble
        self.iforest_detector.fit(historical_df)

        self.is_fitted = True
        logger.info("Successfully fitted SurveillanceEnsembleEngine on %d records.", len(historical_df))
        return self

    def score_record(self, record_df: pd.DataFrame) -> List[SurveillanceInferenceResult]:
        """
        Executes end-to-end ensemble inference across incoming feature records.
        """
        if record_df.empty:
            return []

        if not self.is_fitted:
            # Auto-fit if unfitted
            self.fit(record_df)

        start_time = time.perf_counter()
        results: List[SurveillanceInferenceResult] = []

        # 1. Statistical Baseline evaluation
        baseline_res = self.baseline_detector.detect_anomalies(record_df)

        # 2. Isolation Forest evaluation
        iforest_res = self.iforest_detector.predict_anomalies(record_df)

        # 3. Dynamic Volatility evaluation
        if "close_price" in record_df.columns and "log_return_1d" in record_df.columns:
            cond_vol = self.volatility_forecaster.compute_conditional_volatility(
                record_df["log_return_1d"], annualize=True
            )
            bands = DynamicVolatilityBandGenerator.generate_bands(
                prices=record_df["close_price"],
                conditional_volatility=cond_vol,
                num_std=3.0,
            )
            is_band_breach = bands["is_band_breach"].values
        else:
            is_band_breach = np.zeros(len(record_df), dtype=int)

        total_elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        per_record_latency = total_elapsed_ms / max(1, len(record_df))

        # 4. Compute Weighted Ensemble Score
        base_scores = baseline_res["statistical_anomaly_score"].values
        if_scores = iforest_res["iforest_score"].values
        top_features = iforest_res.get("top_contributing_feature", ["unknown"] * len(record_df))

        for i in range(len(record_df)):
            b_score = float(base_scores[i])
            if_score = float(if_scores[i])
            breach = bool(is_band_breach[i] == 1)

            final_score = (
                self.weight_baseline * b_score
                + self.weight_iforest * if_score
                + self.weight_volatility * (1.0 if breach else 0.0)
            )
            final_score = float(np.clip(final_score, 0.0, 1.0))

            # Tiering:
            # CRITICAL_ALERT: final_score >= 0.70
            # SUSPICIOUS: final_score >= 0.50
            # WATCHLIST: final_score >= 0.30
            # NORMAL: final_score < 0.30
            if final_score >= 0.70:
                tier = "CRITICAL_ALERT"
                is_anom = True
            elif final_score >= 0.50:
                tier = "SUSPICIOUS"
                is_anom = True
            elif final_score >= 0.30:
                tier = "WATCHLIST"
                is_anom = False
            else:
                tier = "NORMAL"
                is_anom = False

            sym = str(record_df["symbol"].iloc[i]) if "symbol" in record_df.columns else "UNKNOWN"
            tdate = str(record_df["trade_date"].iloc[i]) if "trade_date" in record_df.columns else "UNKNOWN"

            results.append(
                SurveillanceInferenceResult(
                    symbol=sym,
                    trade_date=tdate,
                    ensemble_anomaly_score=final_score,
                    severity_tier=tier,
                    is_anomaly=is_anom,
                    baseline_score=b_score,
                    iforest_score=if_score,
                    is_volatility_band_breach=breach,
                    top_contributing_feature=top_features.iloc[i] if hasattr(top_features, "iloc") else top_features[i],
                    execution_time_ms=per_record_latency,
                )
            )

        return results
