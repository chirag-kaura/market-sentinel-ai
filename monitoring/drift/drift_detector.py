"""
Data and Prediction Drift Monitoring Engine.
Phase 11 — Step 11.4: Statistical Kolmogorov-Smirnov and Population Stability Index (PSI) drift detection.
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from pydantic import BaseModel


class DriftMetricResult(BaseModel):
    feature_name: str
    ks_statistic: float
    p_value: float
    psi_score: float
    is_drifted: bool
    drift_level: str  # NONE, MODERATE, CRITICAL


class DriftReport(BaseModel):
    timestamp: str
    sample_size_reference: int
    sample_size_current: int
    overall_drift_detected: bool
    metrics: Dict[str, DriftMetricResult]


class DriftDetector:
    """Statistical drift detector comparing production features against reference baseline distributions."""

    def __init__(self, ks_alpha: float = 0.05, psi_threshold: float = 0.25):
        self.ks_alpha = ks_alpha
        self.psi_threshold = psi_threshold

    def calculate_psi(self, reference: np.ndarray, current: np.ndarray, num_bins: int = 10) -> float:
        """Calculates Population Stability Index (PSI) across quantile buckets."""
        if len(reference) == 0 or len(current) == 0:
            return 0.0

        # Create quantiles based on reference distribution
        quantiles = np.linspace(0, 100, num_bins + 1)
        bin_edges = np.percentile(reference, quantiles)
        bin_edges[0] -= 1e-5
        bin_edges[-1] += 1e-5

        ref_counts, _ = np.histogram(reference, bins=bin_edges)
        cur_counts, _ = np.histogram(current, bins=bin_edges)

        # Smooth zero bins to avoid division by zero
        ref_pct = (ref_counts + 1e-4) / (len(reference) + 1e-4 * num_bins)
        cur_pct = (cur_counts + 1e-4) / (len(current) + 1e-4 * num_bins)

        psi_val = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
        return float(psi_val)

    def analyze_feature_drift(
        self,
        feature_name: str,
        reference_data: List[float],
        current_data: List[float],
    ) -> DriftMetricResult:
        """Evaluates KS 2-sample test and PSI for a numerical surveillance feature."""
        ref_arr = np.array(reference_data, dtype=float)
        cur_arr = np.array(current_data, dtype=float)

        ks_res = ks_2samp(ref_arr, cur_arr)
        psi = self.calculate_psi(ref_arr, cur_arr)

        is_drifted = (ks_res.pvalue < self.ks_alpha) or (psi >= self.psi_threshold)

        if psi >= self.psi_threshold:
            drift_level = "CRITICAL"
        elif ks_res.pvalue < self.ks_alpha or psi >= 0.10:
            drift_level = "MODERATE"
        else:
            drift_level = "NONE"

        return DriftMetricResult(
            feature_name=feature_name,
            ks_statistic=float(ks_res.statistic),
            p_value=float(ks_res.pvalue),
            psi_score=float(psi),
            is_drifted=is_drifted,
            drift_level=drift_level,
        )

    def run_drift_audit(
        self,
        reference_df: pd.DataFrame,
        current_df: pd.DataFrame,
        features: List[str],
    ) -> DriftReport:
        """Runs multi-feature drift audit comparing baseline dataframe to incoming production data."""
        metrics = {}
        any_drift = False

        for feat in features:
            if feat in reference_df.columns and feat in current_df.columns:
                res = self.analyze_feature_drift(
                    feat, reference_df[feat].dropna().tolist(), current_df[feat].dropna().tolist()
                )
                metrics[feat] = res
                if res.is_drifted:
                    any_drift = True

        return DriftReport(
            timestamp=pd.Timestamp.now("UTC").isoformat(),
            sample_size_reference=len(reference_df),
            sample_size_current=len(current_df),
            overall_drift_detected=any_drift,
            metrics=metrics,
        )
