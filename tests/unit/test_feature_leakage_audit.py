"""
Feature Leakage and Look-Ahead Bias Audit Test Suite
Market Sentinel AI — Phase 5: Step 5.7

Programmatically proves zero look-ahead bias and zero data leakage:
1. Future Price Perturbation Test: Modifying prices on date t+k must yield exactly 0.0 change on date t features.
2. Future Volume Perturbation Test: Modifying volume on date t+k must not alter date t volume Z-scores.
3. Post-Market News Leakage Test: Disclosures after 15:30 IST must not be visible on date t.
4. Multi-Symbol Cross-Contamination Test: Shuffling multi-symbol datasets must yield identical features per ticker.
"""

from datetime import date, datetime, timedelta, timezone
import numpy as np
import pandas as pd
import pytest

from processing.features.market_features import MarketFeatureExtractor
from processing.features.multimodal_alignment import MultimodalFeatureAligner
from processing.features.news_features import NewsFeatureExtractor


@pytest.fixture
def base_market_dataset():
    """Generates 30 days of baseline market records for RELIANCE."""
    dates = [date(2026, 3, 1) + timedelta(days=i) for i in range(30)]
    records = []
    base_price = 2500.0
    for i, dt in enumerate(dates):
        records.append({
            "symbol": "RELIANCE",
            "trade_date": dt,
            "open_price": base_price * (1.0 + i * 0.002),
            "high_price": base_price * (1.0 + i * 0.002) * 1.01,
            "low_price": base_price * (1.0 + i * 0.002) * 0.99,
            "close_price": base_price * (1.0 + i * 0.002) * 1.005,
            "total_traded_quantity": 1000000 + i * 5000,
            "delivery_qty": 500000,
        })
    return pd.DataFrame(records)


def test_future_price_perturbation_zero_leakage(base_market_dataset):
    """
    Perturbs day 25 price by 500% and verifies that features on day 15 remain completely identical.
    """
    # 1. Compute features on unmodified dataset
    feats_original = MarketFeatureExtractor.extract_features_for_symbol(base_market_dataset)
    row_day15_orig = feats_original[feats_original["trade_date"] == date(2026, 3, 16)].iloc[0]

    # 2. Perturb future day 25
    perturbed_df = base_market_dataset.copy()
    future_idx = perturbed_df[perturbed_df["trade_date"] == date(2026, 3, 26)].index[0]
    perturbed_df.loc[future_idx, "close_price"] *= 5.0
    perturbed_df.loc[future_idx, "high_price"] *= 5.0

    feats_perturbed = MarketFeatureExtractor.extract_features_for_symbol(perturbed_df)
    row_day15_pert = feats_perturbed[feats_perturbed["trade_date"] == date(2026, 3, 16)].iloc[0]

    # 3. Assert zero leakage
    for col in [
        "log_return_1d",
        "log_return_5d",
        "log_return_20d",
        "volatility_20d",
        "parkinson_volatility_20d",
        "volume_zscore_20d",
        "delivery_ratio",
    ]:
        val_orig = row_day15_orig[col]
        val_pert = row_day15_pert[col]
        if pd.isna(val_orig):
            assert pd.isna(val_pert)
        else:
            assert np.isclose(val_orig, val_pert, atol=1e-12), f"Leakage detected in feature {col}!"


def test_future_volume_perturbation_zero_leakage(base_market_dataset):
    """
    Perturbs future volume on day 28 by 100x and verifies that day 10 volume features are untouched.
    """
    feats_original = MarketFeatureExtractor.extract_features_for_symbol(base_market_dataset)
    row_day10_orig = feats_original[feats_original["trade_date"] == date(2026, 3, 11)].iloc[0]

    perturbed_df = base_market_dataset.copy()
    future_idx = perturbed_df[perturbed_df["trade_date"] == date(2026, 3, 29)].index[0]
    perturbed_df.loc[future_idx, "total_traded_quantity"] *= 100

    feats_perturbed = MarketFeatureExtractor.extract_features_for_symbol(perturbed_df)
    row_day10_pert = feats_perturbed[feats_perturbed["trade_date"] == date(2026, 3, 11)].iloc[0]

    assert np.isclose(row_day10_orig["volume_zscore_20d"], row_day10_pert["volume_zscore_20d"], atol=1e-12)
    assert np.isclose(row_day10_orig["volume_mean_20d"], row_day10_pert["volume_mean_20d"], atol=1e-12)


def test_post_market_news_leakage_boundary():
    """
    Verifies that a news article released 1 minute after market close (15:31 IST / 10:01 UTC)
    on date t is strictly rolled over to date t+1 and is completely invisible on date t.
    """
    # Publication at 10:01 UTC on March 30, 2026 (15:31 IST)
    post_market_time = datetime(2026, 3, 30, 10, 1, 0, tzinfo=timezone.utc)
    articles = [{
        "title": "Reliance announces surprise Q4 earnings beat",
        "published_at_utc": post_market_time.isoformat(),
        "detected_symbols": ["RELIANCE"],
    }]

    news_features = NewsFeatureExtractor.extract_daily_news_features(articles)
    assert len(news_features) == 1
    # Rolled over to March 31
    assert news_features["trade_date"].iloc[0] == date(2026, 3, 31)

    # Align with market dates for March 30 and March 31
    m_df = pd.DataFrame([
        {
            "symbol": "RELIANCE",
            "trade_date": date(2026, 3, 30),
            "close_price": 2500.0,
            "open_price": 2490.0,
            "high_price": 2510.0,
            "low_price": 2480.0,
            "total_traded_quantity": 1000000,
            "delivery_qty": 500000,
            "log_return_1d": 0.005,
        },
        {
            "symbol": "RELIANCE",
            "trade_date": date(2026, 3, 31),
            "close_price": 2550.0,
            "open_price": 2540.0,
            "high_price": 2560.0,
            "low_price": 2530.0,
            "total_traded_quantity": 2000000,
            "delivery_qty": 1000000,
            "log_return_1d": 0.02,
        },
    ])

    aligned = MultimodalFeatureAligner.align_features(m_df, news_features)

    # March 30 must have 0 news count (no leak from post-market disclosure)
    row_day30 = aligned[aligned["trade_date"] == date(2026, 3, 30)].iloc[0]
    assert row_day30["news_count_1d"] == 0

    # March 31 must reflect the news
    row_day31 = aligned[aligned["trade_date"] == date(2026, 3, 31)].iloc[0]
    assert row_day31["news_count_1d"] == 1


def test_multi_symbol_independence_and_no_cross_contamination(base_market_dataset):
    """
    Verifies that grouping and interleaving multiple symbols yields identical
    rolling feature calculations compared to evaluating the symbol in isolation.
    """
    rel_df = base_market_dataset.copy()
    tcs_df = base_market_dataset.copy()
    tcs_df["symbol"] = "TCS"
    tcs_df["close_price"] *= 1.4

    # Interleave rows randomly
    combined_df = pd.concat([rel_df, tcs_df]).sample(frac=1.0, random_state=42).reset_index(drop=True)

    bulk_features = MarketFeatureExtractor.extract_features_bulk(combined_df)
    rel_isolated = MarketFeatureExtractor.extract_features_for_symbol(rel_df)

    # Compare RELIANCE from bulk vs isolated
    rel_from_bulk = bulk_features[bulk_features["symbol"] == "RELIANCE"].sort_values("trade_date").reset_index(drop=True)
    rel_isolated = rel_isolated.sort_values("trade_date").reset_index(drop=True)

    pd.testing.assert_series_equal(rel_from_bulk["volatility_20d"], rel_isolated["volatility_20d"])
    pd.testing.assert_series_equal(rel_from_bulk["volume_zscore_20d"], rel_isolated["volume_zscore_20d"])
