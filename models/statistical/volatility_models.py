"""
Volatility Forecasting & Clustering Engine (Phase 6 — Step 6.3)
Market Sentinel AI — Quantitative Surveillance Models

Implements conditional time-varying volatility models:
- RiskMetrics EWMA Volatility (lambda = 0.94) for recursive conditional variance.
- GARCH(1,1) Conditional Volatility Model (omega + alpha*r^2 + beta*sigma^2).
- Dynamic Volatility Envelopes for regime-adaptive surveillance alerting.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

logger = logging.getLogger("market_sentinel.models.statistical.volatility_models")
logger.setLevel(logging.INFO)


@dataclass
class GARCHParams:
    omega: float
    alpha: float
    beta: float
    is_stationary: bool

    @property
    def persistence(self) -> float:
        return self.alpha + self.beta


class EWMAVolatilityForecaster:
    """
    Computes RiskMetrics Exponentially Weighted Moving Average (EWMA) volatility:
    sigma_t^2 = lambda * sigma_{t-1}^2 + (1 - lambda) * r_{t-1}^2
    """

    def __init__(self, decay_factor: float = 0.94):
        self.decay_factor = decay_factor

    def compute_conditional_volatility(
        self,
        returns: pd.Series,
        annualize: bool = True,
    ) -> pd.Series:
        """
        Recursively calculates conditional standard deviation for a returns series.
        """
        if returns.empty:
            return pd.Series(dtype=float)

        clean_ret = returns.fillna(0.0).values
        n = len(clean_ret)
        variance = np.zeros(n)

        # Initialize with sample variance of the first 10 observations or 0.0002
        init_var = np.var(clean_ret[:min(10, n)]) if n >= 2 else 0.0002
        if init_var <= 0:
            init_var = 0.0002
        variance[0] = init_var

        # Recursive EWMA update
        lam = self.decay_factor
        one_minus_lam = 1.0 - lam

        for t in range(1, n):
            prev_r_sq = clean_ret[t - 1] ** 2
            variance[t] = lam * variance[t - 1] + one_minus_lam * prev_r_sq

        std_dev = np.sqrt(np.maximum(variance, 1e-8))
        if annualize:
            std_dev = std_dev * np.sqrt(252)

        return pd.Series(std_dev, index=returns.index, name="ewMA_volatility")


class GARCHVolatilityModel:
    """
    Fits standard GARCH(1,1) model:
    sigma_t^2 = omega + alpha * r_{t-1}^2 + beta * sigma_{t-1}^2
    """

    def __init__(self):
        self.params: Optional[GARCHParams] = None

    @staticmethod
    def _neg_log_likelihood(params: np.ndarray, returns: np.ndarray) -> float:
        """Negative log-likelihood of GARCH(1,1) under Gaussian assumptions."""
        omega, alpha, beta = params
        n = len(returns)
        variance = np.zeros(n)
        variance[0] = np.var(returns) if np.var(returns) > 0 else 0.0002

        for t in range(1, n):
            variance[t] = omega + alpha * (returns[t - 1] ** 2) + beta * variance[t - 1]
            if variance[t] <= 0:
                return 1e10

        # Gaussian log-likelihood
        ll = -0.5 * np.sum(np.log(2 * np.pi) + np.log(variance) + (returns ** 2) / variance)
        return -ll

    def fit(self, returns: pd.Series) -> GARCHVolatilityModel:
        """
        Fits GARCH(1,1) parameters using maximum likelihood optimization.
        """
        clean_ret = returns.dropna().values
        if len(clean_ret) < 25:
            # Fallback to standard calibrated parameters if series too short
            self.params = GARCHParams(omega=1e-5, alpha=0.08, beta=0.88, is_stationary=True)
            return self

        sample_var = float(np.var(clean_ret))
        # Initial guess: omega = 0.04 * sample_var, alpha = 0.08, beta = 0.88
        init_guess = [0.04 * sample_var, 0.08, 0.88]
        bounds = [(1e-7, None), (0.001, 0.30), (0.50, 0.98)]
        # Constraint: alpha + beta < 0.999 (covariance stationarity)
        constraints = {"type": "ineq", "fun": lambda p: 0.999 - (p[1] + p[2])}

        try:
            opt_res = minimize(
                self._neg_log_likelihood,
                init_guess,
                args=(clean_ret,),
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                options={"maxiter": 100, "ftol": 1e-6},
            )
            if opt_res.success:
                om, al, be = opt_res.x
                self.params = GARCHParams(
                    omega=float(om),
                    alpha=float(al),
                    beta=float(be),
                    is_stationary=bool((al + be) < 1.0),
                )
            else:
                self.params = GARCHParams(omega=0.04 * sample_var, alpha=0.08, beta=0.88, is_stationary=True)
        except Exception as err:
            logger.warning("GARCH numerical optimization failed (%s). Using fallback calibration.", err)
            self.params = GARCHParams(omega=0.04 * sample_var, alpha=0.08, beta=0.88, is_stationary=True)

        return self

    def forecast_conditional_volatility(
        self,
        returns: pd.Series,
        annualize: bool = True,
    ) -> pd.Series:
        """
        Computes conditional volatility series using fitted GARCH(1,1) parameters.
        """
        if self.params is None:
            self.fit(returns)

        p = self.params or GARCHParams(omega=1e-5, alpha=0.08, beta=0.88, is_stationary=True)
        clean_ret = returns.fillna(0.0).values
        n = len(clean_ret)
        variance = np.zeros(n)
        variance[0] = np.var(clean_ret) if len(clean_ret) > 1 and np.var(clean_ret) > 0 else 0.0002

        for t in range(1, n):
            variance[t] = p.omega + p.alpha * (clean_ret[t - 1] ** 2) + p.beta * variance[t - 1]

        std_dev = np.sqrt(np.maximum(variance, 1e-8))
        if annualize:
            std_dev = std_dev * np.sqrt(252)

        return pd.Series(std_dev, index=returns.index, name="garch_volatility")


class DynamicVolatilityBandGenerator:
    """
    Computes dynamic surveillance bands scaling anomaly thresholds to market volatility regimes.
    Enforces non-negative sorted confidence bounds (Issue 17).
    """

    @staticmethod
    def generate_bands(
        prices: pd.Series,
        conditional_volatility: pd.Series,
        num_std: float = 3.0,
    ) -> pd.DataFrame:
        """
        Generates dynamic price bands: Upper = P_{t-1} * (1 + k*sigma_t), Lower = P_{t-1} * (1 - k*sigma_t).
        Guarantees upper >= lower >= 0.0 to satisfy database and mathematical constraints.
        """
        df = pd.DataFrame(index=prices.index)
        df["price"] = prices
        # Daily standard deviation = annualized_volatility / sqrt(252)
        daily_sigma = conditional_volatility / np.sqrt(252)

        prev_price = prices.shift(1).bfill()
        raw_upper = prev_price * (1.0 + num_std * daily_sigma)
        raw_lower = np.maximum(0.0, prev_price * (1.0 - num_std * daily_sigma))

        # Enforce sorted non-negative bounds
        df["dynamic_upper_band"] = np.maximum(raw_upper, raw_lower)
        df["dynamic_lower_band"] = np.minimum(raw_upper, raw_lower)
        df["is_band_breach"] = (
            (prices > df["dynamic_upper_band"]) | (prices < df["dynamic_lower_band"])
        ).astype(int)

        return df


class GJRGARCHVolatilityModel:
    """
    Asymmetric GJR-GARCH(1,1) model capturing leverage effects (Glosten, Jagannathan, Runkle 1993):
    sigma_t^2 = omega + (alpha + gamma * I_{r_{t-1} < 0}) * r_{t-1}^2 + beta * sigma_{t-1}^2
    Empirically models heightened downside volatility shocks preceding regulatory events.
    """

    def __init__(self, omega: float = 1e-5, alpha: float = 0.05, gamma: float = 0.08, beta: float = 0.85):
        self.omega = omega
        self.alpha = alpha
        self.gamma = gamma
        self.beta = beta

    def compute_conditional_volatility(self, returns: pd.Series, annualize: bool = True) -> pd.Series:
        clean_ret = returns.fillna(0.0).values
        n = len(clean_ret)
        variance = np.zeros(n)
        variance[0] = np.var(clean_ret) if len(clean_ret) > 1 and np.var(clean_ret) > 0 else 0.0002

        for t in range(1, n):
            r_prev = clean_ret[t - 1]
            leverage_indicator = 1.0 if r_prev < 0 else 0.0
            variance[t] = (
                self.omega
                + (self.alpha + self.gamma * leverage_indicator) * (r_prev ** 2)
                + self.beta * variance[t - 1]
            )

        std_dev = np.sqrt(np.maximum(variance, 1e-8))
        if annualize:
            std_dev = std_dev * np.sqrt(252)
        return pd.Series(std_dev, index=returns.index, name="gjr_garch_volatility")
