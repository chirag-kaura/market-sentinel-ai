"""
Unit Tests for Market Feature Engineering Pipeline
Market Sentinel AI — Phase 5: Step 5.2
"""

from datetime import date, timedelta
import numpy as np
import pandas as pd
import pytest

from processing.features.market_features import MarketFeatureExtractor


@pytest.fixture
def sample_market_df():
    """Generates 40 trading days of realistic market data for 2 symbols."""
    dates = [date(2026, 1, 1) + timedelta(days=i) for i in range(40)]
    records = []
    
    for sym in ["RELIANCE", "TCS"]:
        base_price = 2500.0 if sym == "RELIANCE" else 3500.0
        for i, dt in enumerate(dates):
            close_p = base_price * (1.0 + (i * 0.005))
            open_p = close_p * 0.99
            high_p = close_p * 1.02
            low_p = close_p * 0.98
            volume = 1000000 + (i * 10000)
            delivery = int(volume * 0.55)

            records.append({
                "symbol": sym,
                "trade_date": dt,
                "open_price": open_p,
                "high_price": high_p,
                "low_price": low_p,
                "close_price": close_p,
                "total_traded_quantity": volume,
                "delivery_qty": delivery,
            })

    return pd.DataFrame(records)


def test_extract_features_for_single_symbol(sample_market_df):
    rel_df = sample_market_df[sample_market_df["symbol"] == "RELIANCE"]
    feats = MarketFeatureExtractor.extract_features_for_symbol(rel_df, rolling_window=20)

    assert len(feats) == 40
    assert "log_return_1d" in feats.columns
    assert "log_return_5d" in feats.columns
    assert "log_return_20d" in feats.columns
    assert "volatility_20d" in feats.columns
    assert "parkinson_volatility_20d" in feats.columns
    assert "volume_zscore_20d" in feats.columns
    assert "delivery_ratio" in feats.columns
    assert "delivery_ratio_zscore_20d" in feats.columns

    # Verify mathematical properties
    # Parkinson volatility must be positive once past min_periods
    valid_parkinson = feats["parkinson_volatility_20d"].dropna()
    assert (valid_parkinson > 0.0).all()

    # Delivery ratio should be around 0.55
    valid_deliv = feats["delivery_ratio"].dropna()
    assert ((valid_deliv >= 0.0) & (valid_deliv <= 1.0)).all()
    assert abs(valid_deliv.mean() - 0.55) < 0.01


def test_extract_features_bulk(sample_market_df):
    bulk_feats = MarketFeatureExtractor.extract_features_bulk(sample_market_df, rolling_window=20)
    assert len(bulk_feats) == 80  # 40 days * 2 symbols
    assert set(bulk_feats["symbol"].unique()) == {"RELIANCE", "TCS"}

    # Ensure no symbol cross-contamination in rolling windows
    for sym in ["RELIANCE", "TCS"]:
        sym_sub = bulk_feats[bulk_feats["symbol"] == sym]
        assert len(sym_sub) == 40
        assert sym_sub["trade_date"].is_monotonic_increasing


def test_extract_features_empty_dataframe():
    empty_df = pd.DataFrame()
    assert MarketFeatureExtractor.extract_features_for_symbol(empty_df).empty
    assert MarketFeatureExtractor.extract_features_bulk(empty_df).empty
