"""
Unit Tests for Time-Varying Volatility Forecasting Models
Market Sentinel AI — Phase 6: Step 6.3
"""

import numpy as np
import pandas as pd
import pytest

from models.statistical.volatility_models import (
    DynamicVolatilityBandGenerator,
    EWMAVolatilityForecaster,
    GARCHVolatilityModel,
)


@pytest.fixture
def sample_returns_series():
    """Generates 100 days of log returns with volatility clustering (GARCH-like)."""
    np.random.seed(42)
    n = 100
    returns = np.zeros(n)
    sigma = 0.015
    for t in range(n):
        # Volatility clustering: large shocks increase future volatility
        if t in [30, 31, 32]:
            sigma = 0.04
        else:
            sigma = 0.012 + 0.5 * abs(returns[t - 1]) if t > 0 else 0.015
        returns[t] = np.random.normal(0.0005, sigma)
    return pd.Series(returns, name="log_return_1d")


def test_ewma_volatility_forecaster(sample_returns_series):
    forecaster = EWMAVolatilityForecaster(decay_factor=0.94)
    vol = forecaster.compute_conditional_volatility(sample_returns_series, annualize=True)

    assert len(vol) == len(sample_returns_series)
    assert (vol > 0.0).all()
    # During high shock days (t=30-35), EWMA volatility must rise
    assert vol.iloc[35] > vol.iloc[20]


def test_garch_volatility_model_fit_and_forecast(sample_returns_series):
    model = GARCHVolatilityModel()
    model.fit(sample_returns_series)

    assert model.params is not None
    assert model.params.omega > 0.0
    assert model.params.alpha > 0.0
    assert model.params.beta > 0.0
    # Stationarity condition: alpha + beta < 1.0
    assert model.params.persistence < 1.0
    assert model.params.is_stationary is True

    forecast = model.forecast_conditional_volatility(sample_returns_series, annualize=True)
    assert len(forecast) == len(sample_returns_series)
    assert (forecast > 0.0).all()


def test_dynamic_volatility_bands(sample_returns_series):
    forecaster = EWMAVolatilityForecaster()
    cond_vol = forecaster.compute_conditional_volatility(sample_returns_series, annualize=True)

    # Reconstruct prices from returns
    base_price = 1000.0
    prices = pd.Series(base_price * np.exp(np.cumsum(sample_returns_series)), name="close_price")

    bands = DynamicVolatilityBandGenerator.generate_bands(
        prices=prices,
        conditional_volatility=cond_vol,
        num_std=3.0,
    )

    assert len(bands) == len(prices)
    assert "dynamic_upper_band" in bands.columns
    assert "dynamic_lower_band" in bands.columns
    assert "is_band_breach" in bands.columns

    # Upper band must strictly be higher than lower band
    assert (bands["dynamic_upper_band"] > bands["dynamic_lower_band"]).all()


def test_volatility_empty_series():
    forecaster = EWMAVolatilityForecaster()
    assert forecaster.compute_conditional_volatility(pd.Series(dtype=float)).empty

    model = GARCHVolatilityModel()
    # Small series fallback
    model.fit(pd.Series([0.01, -0.01, 0.02]))
    assert model.params.is_stationary is True
