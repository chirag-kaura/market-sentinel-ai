"""
Unit Tests for Financial Market Exploratory Data Analysis (EDA) Engine
Market Sentinel AI — Phase 5: Step 5.1
"""

from datetime import date, timedelta
import numpy as np
import pandas as pd
import pytest

from processing.eda.market_eda import MarketEDAProfiler, MarketSeriesProfile


@pytest.fixture
def sample_market_series():
    """Generates a reproducible 60-day price series with fat tails for unit testing."""
    np.random.seed(42)
    start_date = date(2026, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(60)]
    
    # Generate prices with heavy tails and negative drift
    base_price = 1000.0
    shocks = np.random.standard_t(df=3, size=60) * 0.02
    prices = [base_price]
    for shock in shocks[1:]:
        prices.append(prices[-1] * (1.0 + shock))

    turnover = np.random.uniform(5e7, 2e8, size=60)  # 5 Cr to 20 Cr
    delivery_ratio = np.random.uniform(0.40, 0.70, size=60)

    return pd.DataFrame({
        "symbol": "RELIANCE",
        "trade_date": dates,
        "close_price": prices,
        "total_turnover": turnover,
        "delivery_to_traded_ratio": delivery_ratio,
    })


def test_compute_log_returns(sample_market_series):
    log_returns = MarketEDAProfiler.compute_log_returns(sample_market_series)
    assert len(log_returns) == 59  # 60 days produces 59 daily returns
    assert isinstance(log_returns, pd.Series)
    # Mean daily log return should be near 0
    assert abs(log_returns.mean()) < 0.10


def test_profile_symbol_series_metrics(sample_market_series):
    profile = MarketEDAProfiler.profile_symbol_series(
        symbol="RELIANCE",
        df=sample_market_series,
    )
    assert isinstance(profile, MarketSeriesProfile)
    assert profile.symbol == "RELIANCE"
    assert profile.record_count == 60
    assert profile.annualized_volatility > 0.0
    assert profile.avg_turnover_cr > 0.0
    assert 0.0 <= profile.avg_delivery_pct <= 1.0
    # Fat-tailed distribution (Student-t degrees of freedom 3) will have high kurtosis
    assert profile.excess_kurtosis > 0.0
    assert profile.jarque_bera_stat >= 0.0


def test_profile_empty_or_small_series():
    # 2-day series -> 1 return -> handles gracefully
    small_df = pd.DataFrame({
        "symbol": "TCS",
        "trade_date": [date(2026, 1, 1), date(2026, 1, 2)],
        "close_price": [3500.0, 3520.0],
    })
    profile = MarketEDAProfiler.profile_symbol_series("TCS", small_df)
    assert profile.symbol == "TCS"
    assert profile.annualized_volatility == 0.0


def test_generate_eda_summary_table(sample_market_series):
    p1 = MarketEDAProfiler.profile_symbol_series("RELIANCE", sample_market_series)
    summary_df = MarketEDAProfiler.generate_eda_summary_table([p1])
    assert len(summary_df) == 1
    assert "annualized_volatility" in summary_df.columns
    assert "excess_kurtosis" in summary_df.columns
    assert "jarque_bera_stat" in summary_df.columns
