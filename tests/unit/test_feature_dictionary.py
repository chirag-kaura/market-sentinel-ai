"""
Unit Tests for Feature Dictionary Consistency & Schema Parity
Market Sentinel AI — Phase 5: Step 5.6
"""

from datetime import date
from pathlib import Path
import re
import pandas as pd
import pytest

from processing.features.market_features import MarketFeatureExtractor
from processing.features.multimodal_alignment import MultimodalFeatureAligner
from processing.features.news_features import NewsFeatureExtractor


def test_feature_dictionary_markdown_exists():
    dict_path = Path("docs/data/feature_dictionary.md")
    assert dict_path.exists()
    assert dict_path.stat().st_size > 1000


def test_feature_dictionary_code_schema_parity():
    """
    Parses `docs/data/feature_dictionary.md` to extract all documented feature names,
    and verifies that every documented feature is produced by the feature engineering pipeline.
    """
    dict_path = Path("docs/data/feature_dictionary.md")
    with open(dict_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract all `feature_name` from markdown tables
    documented_features = set(re.findall(r"\|\s*`([a-zA-Z0-9_]+)`\s*\|\s*`", content))
    assert len(documented_features) >= 20

    # Build dummy market data
    dates = [date(2026, 3, 20) + pd.Timedelta(days=i) for i in range(25)]
    market_records = []
    for dt in dates:
        market_records.append({
            "symbol": "RELIANCE",
            "trade_date": dt,
            "open_price": 2500.0,
            "high_price": 2550.0,
            "low_price": 2480.0,
            "close_price": 2520.0,
            "total_traded_quantity": 1000000,
            "delivery_qty": 550000,
        })
    m_df = pd.DataFrame(market_records)
    market_features = MarketFeatureExtractor.extract_features_for_symbol(m_df, rolling_window=20)

    # Build dummy news data
    news_articles = [{
        "title": "Reliance green energy expansion wins major approval",
        "summary": "Record investments announced.",
        "published_at_utc": "2026-03-30T07:00:00+00:00",
        "detected_symbols": ["RELIANCE"],
    }]
    news_features = NewsFeatureExtractor.extract_daily_news_features(news_articles)

    # Align features
    aligned_df = MultimodalFeatureAligner.align_features(market_features, news_features)

    # Verify every documented feature exists in the aligned output
    produced_columns = set(aligned_df.columns)
    for feat in documented_features:
        assert feat in produced_columns, f"Documented feature '{feat}' is missing from aligned output columns!"


def test_feature_types_and_no_unexpected_nulls():
    """
    Ensures that essential cross-modal interaction indicators do not produce unhandled NaNs.
    """
    dates = [date(2026, 3, 20) + pd.Timedelta(days=i) for i in range(25)]
    m_df = pd.DataFrame([{
        "symbol": "TCS",
        "trade_date": dt,
        "open_price": 3500.0,
        "high_price": 3550.0,
        "low_price": 3480.0,
        "close_price": 3520.0,
        "total_traded_quantity": 500000,
        "delivery_qty": 300000,
    } for dt in dates])
    market_features = MarketFeatureExtractor.extract_features_for_symbol(m_df, rolling_window=20)
    aligned_df = MultimodalFeatureAligner.align_features(market_features, None)

    # Cross-modal flags should not have nulls
    assert aligned_df["news_price_divergence"].notna().all()
    assert aligned_df["volume_news_divergence"].notna().all()
    assert aligned_df["sentiment_return_alignment"].notna().all()
    assert aligned_df["is_unbacked_market_move"].notna().all()
