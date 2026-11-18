"""Unit tests for Automated Data Cleaning and Deduplication Modules."""
from datetime import date
from decimal import Decimal
import pandas as pd
import pytest

from processing.pandas.market_cleaner import MarketDataCleaner
from processing.pandas.news_deduplicator import NewsDeduplicator


def test_market_cleaner_deduplication_and_validation():
    """Test price boundary validation and duplicate resolution in MarketDataCleaner."""
    records = [
        # Valid quote 1
        {
            "symbol": "RELIANCE",
            "trade_date": "2026-11-17",
            "open_price": 2450.0,
            "high_price": 2480.0,
            "low_price": 2440.0,
            "close_price": 2470.0,
            "volume": 5000000,
            "turnover": 12350000000.0,
            "delivery_qty": 2500000,
            "delivery_pct": 50.0,
        },
        # Duplicate quote (same symbol and date, updated volume) -> should overwrite
        {
            "symbol": "RELIANCE",
            "trade_date": "2026-11-17",
            "open_price": 2450.0,
            "high_price": 2485.0,
            "low_price": 2440.0,
            "close_price": 2475.0,
            "volume": 5200000,
            "turnover": 12850000000.0,
            "delivery_qty": 2600000,
            "delivery_pct": 50.0,
        },
        # Corrupted quote (high < low) -> should be quarantined
        {
            "symbol": "TCS",
            "trade_date": "2026-11-17",
            "open_price": 4100.0,
            "high_price": 4050.0,  # Corrupted: high < low
            "low_price": 4120.0,
            "close_price": 4080.0,
            "volume": 1000000,
            "turnover": 4100000000.0,
        },
        # Valid quote 2
        {
            "symbol": "INFY",
            "trade_date": "2026-11-17",
            "open_price": 1850.0,
            "high_price": 1870.0,
            "low_price": 1840.0,
            "close_price": 1860.0,
            "volume": 2000000,
            "turnover": 3720000000.0,
        }
    ]

    df, metrics = MarketDataCleaner.clean_quotes(records)

    assert metrics["initial_rows"] == 4
    assert metrics["corrupted_rows_quarantined"] == 1  # TCS corrupted
    assert metrics["duplicates_removed"] == 1  # RELIANCE duplicate resolved
    assert metrics["final_clean_rows"] == 2  # RELIANCE + INFY clean

    assert len(df) == 2
    rel = df[df["symbol"] == "RELIANCE"].iloc[0]
    assert rel["close_price"] == 2475.0
    assert rel["high_price"] == 2485.0


def test_news_deduplicator_url_and_syndicate_matching():
    """Test exact URL normalization and syndicate headline deduplication."""
    articles = [
        # Original article
        {
            "canonical_url": "https://economictimes.indiatimes.com/stocks/tatamotors-jlr-surge?utm_source=rss&ref=feed",
            "title": "Tata Motors shares surge 6% on strong JLR deliveries",
            "source_outlet": "Economic Times",
        },
        # Duplicate 1: Same article with different tracking parameters
        {
            "canonical_url": "https://economictimes.indiatimes.com/stocks/tatamotors-jlr-surge?utm_medium=twitter",
            "title": "Tata Motors shares surge 6% on strong JLR deliveries",
            "source_outlet": "Economic Times",
        },
        # Duplicate 2: Syndicated reprint with slightly different spacing/punctuation
        {
            "canonical_url": "https://moneycontrol.com/news/tatamotors-reprint",
            "title": "Tata Motors shares surge 6% on strong JLR deliveries!",
            "source_outlet": "Moneycontrol",
        },
        # Unique article
        {
            "canonical_url": "https://economictimes.indiatimes.com/stocks/infosys-results",
            "title": "Infosys quarterly revenue beats analyst estimates by 4%",
            "source_outlet": "Economic Times",
        }
    ]

    unique, duplicates, metrics = NewsDeduplicator.deduplicate_articles(articles)

    assert metrics["total_input"] == 4
    assert metrics["exact_url_duplicates"] == 1  # Stripped tracking params matched
    assert metrics["syndicate_headline_duplicates"] == 1  # Identical alphanumeric hash matched
    assert metrics["retained_unique"] == 2  # 1 Tata Motors + 1 Infosys

    assert len(unique) == 2
    assert unique[0]["canonical_url"] == "https://economictimes.indiatimes.com/stocks/tatamotors-jlr-surge"
