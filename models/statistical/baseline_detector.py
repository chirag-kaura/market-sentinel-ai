"""
Statistical Baseline Anomaly Detection Engine (Phase 6 — Step 6.1)
Market Sentinel AI — Quantitative Surveillance Models

Implements auditable, non-parametric statistical baseline surveillance detectors:
- Rolling Z-score anomaly bounds for 1d return and 20d volume.
- Non-parametric empirical percentile cutoffs (P95, P99, P99.9) calibrated for fat tails.
- Delivery divergence anomaly detection (high volume surge + low delivery percentage).
- Deterministic severity tiering (NORMAL, WATCHLIST, SUSPICIOUS, ALERT) with [0.0, 1.0] score.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("market_sentinel.models.statistical.baseline_detector")
logger.setLevel(logging.INFO)


@dataclass
class AnomalyThresholdConfig:
    return_zscore_critical: float = 3.0
    return_zscore_high: float = 2.0
    volume_zscore_critical: float = 3.0
    volume_zscore_high: float = 2.0
    delivery_divergence_vol_z: float = 2.5
    delivery_divergence_max_ratio: float = 0.30
    unbacked_move_divergence_min: float = 0.03


class StatisticalBaselineDetector:
    """
    Evaluates market time-series records against statistical thresholds and empirical bounds.
    """

    def __init__(self, config: Optional[AnomalyThresholdConfig] = None):
        self.config = config or AnomalyThresholdConfig()
        self.empirical_percentiles: Dict[str, Dict[str, float]] = {}
        self.is_fitted = False

    def fit(self, df: pd.DataFrame) -> StatisticalBaselineDetector:
        """
        Calibrates empirical non-parametric percentile boundaries (P95, P99, P99.9)
        from historical data.
        """
        if df.empty:
            logger.warning("Empty dataframe provided to fit. Skipping percentile calibration.")
            return self

        for col in ["log_return_1d", "volume_zscore_20d", "news_price_divergence"]:
            if col in df.columns:
                valid_vals = df[col].dropna().abs()
                if not valid_vals.empty:
                    self.empirical_percentiles[col] = {
                        "p95": float(np.percentile(valid_vals, 95)),
                        "p99": float(np.percentile(valid_vals, 99)),
                        "p99_9": float(np.percentile(valid_vals, 99.9)),
                    }

        self.is_fitted = True
        logger.info("Fitted empirical percentile thresholds: %s", self.empirical_percentiles)
        return self

    def detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes anomaly flags, statistical scores in [0.0, 1.0], and severity tiers.
        """
        if df.empty:
            return pd.DataFrame()

        res = df.copy()

        # 1. Price Return Anomaly Flags
        ret_series = res["log_return_1d"].fillna(0.0) if "log_return_1d" in res.columns else pd.Series(0.0, index=res.index)
        abs_ret = ret_series.abs()

        # Approximate return z-score using 20d volatility if available, or sample std
        if "volatility_20d" in res.columns:
            # Daily sigma = annualized / sqrt(252)
            daily_sigma = (res["volatility_20d"] / np.sqrt(252)).replace(0, np.nan).fillna(0.015)
            ret_zscore = abs_ret / daily_sigma
        else:
            std_val = abs_ret.std() or 0.015
            ret_zscore = abs_ret / std_val
        res["return_zscore"] = ret_zscore.round(4)

        # 2. Volume Anomaly Flags
        vol_zscore = res["volume_zscore_20d"].fillna(0.0) if "volume_zscore_20d" in res.columns else pd.Series(0.0, index=res.index)

        # 3. Delivery Divergence Flag: high volume Z-score (> 2.5) with low delivery ratio (< 30%)
        deliv_ratio = res["delivery_ratio"].fillna(0.50) if "delivery_ratio" in res.columns else pd.Series(0.50, index=res.index)
        deliv_divergence = (
            (vol_zscore >= self.config.delivery_divergence_vol_z)
            & (deliv_ratio <= self.config.delivery_divergence_max_ratio)
        ).astype(int)
        res["delivery_divergence_flag"] = deliv_divergence

        # 4. Empirical Tail Flags
        p99_ret = self.empirical_percentiles.get("log_return_1d", {}).get("p99", 0.04)
        p99_vol = self.empirical_percentiles.get("volume_zscore_20d", {}).get("p99", 3.0)
        res["return_p99_flag"] = (abs_ret >= p99_ret).astype(int)
        res["volume_p99_flag"] = (vol_zscore >= p99_vol).astype(int)

        # 5. Composite Anomaly Score in [0.0, 1.0]
        # Weighted mixture: 35% return z-score, 35% volume z-score, 20% delivery divergence, 10% unbacked move
        unbacked_flag = res.get("is_unbacked_market_move", pd.Series(0, index=res.index)).fillna(0)

        raw_score = (
            (ret_zscore / 4.0).clip(0.0, 1.0) * 0.35
            + (vol_zscore / 4.0).clip(0.0, 1.0) * 0.35
            + deliv_divergence * 0.20
            + unbacked_flag * 0.10
        )
        res["statistical_anomaly_score"] = raw_score.round(4)

        # 6. Categorical Severity Tiering
        # ALERT: score >= 0.70 or (return_z >= 3.0 and volume_z >= 3.0)
        # SUSPICIOUS: score >= 0.45
        # WATCHLIST: score >= 0.25
        # NORMAL: score < 0.25
        conditions = [
            (res["statistical_anomaly_score"] >= 0.70) | ((ret_zscore >= 3.0) & (vol_zscore >= 3.0)),
            res["statistical_anomaly_score"] >= 0.45,
            res["statistical_anomaly_score"] >= 0.25,
        ]
        choices = ["ALERT", "SUSPICIOUS", "WATCHLIST"]
        res["severity_tier"] = np.select(conditions, choices, default="NORMAL")

        return res
