"""
Unit Tests for News & Corporate Disclosures Feature Engineering Pipeline
Market Sentinel AI — Phase 5: Step 5.4
"""

from datetime import date, datetime, timedelta, timezone
import pytest

from processing.features.news_features import NewsFeatureExtractor


def test_attribute_to_trading_date_intraday_vs_post_market():
    # 08:00 UTC (13:30 IST) -> Intraday -> Same trade date
    intraday_time = datetime(2026, 3, 30, 8, 0, 0, tzinfo=timezone.utc)
    target_dt = NewsFeatureExtractor.attribute_to_trading_date(intraday_time)
    assert target_dt == date(2026, 3, 30)

    # 11:30 UTC (17:00 IST) -> Post-Market -> Rollover to next calendar day
    post_market_time = datetime(2026, 3, 30, 11, 30, 0, tzinfo=timezone.utc)
    target_dt_next = NewsFeatureExtractor.attribute_to_trading_date(post_market_time)
    assert target_dt_next == date(2026, 3, 31)


def test_calculate_text_sentiment_lexicon():
    positive_text = "Reliance Q4 profit beats estimates with record dividend growth"
    pos_score = NewsFeatureExtractor.calculate_text_sentiment(positive_text)
    assert pos_score > 0.0

    negative_text = "TCS quarterly loss warning triggers sharp decline and fine penalty"
    neg_score = NewsFeatureExtractor.calculate_text_sentiment(negative_text)
    assert neg_score < 0.0

    neutral_text = "Company scheduled annual shareholder meeting for upcoming quarter"
    neu_score = NewsFeatureExtractor.calculate_text_sentiment(neutral_text)
    assert neu_score == 0.0


def test_extract_daily_news_features():
    base_time = datetime(2026, 3, 30, 7, 0, 0, tzinfo=timezone.utc)  # Market hours
    news_articles = [
        {
            "title": "Reliance green energy expansion wins major approval",
            "summary": "Record investments announced.",
            "published_at_utc": base_time.isoformat(),
            "detected_symbols": ["RELIANCE"],
        },
        {
            "title": "Reliance retail branch growth surges",
            "summary": "Expansion into 50 new cities.",
            "published_at_utc": (base_time + timedelta(hours=1)).isoformat(),
            "detected_symbols": ["RELIANCE"],
        },
        {
            "title": "TCS cloud contract win in North America",
            "summary": "Multi-year deal signed.",
            "published_at_utc": base_time.isoformat(),
            "detected_symbols": ["TCS"],
        },
    ]

    corporate_disclosures = [
        {
            "symbol": "RELIANCE",
            "announcement_type": "Financial Results for Q4",
            "filing_date_utc": base_time.isoformat(),
        },
        {
            "symbol": "TCS",
            "announcement_type": "Notice of Board Meeting to consider dividend",
            "filing_date_utc": base_time.isoformat(),
        },
    ]

    features_df = NewsFeatureExtractor.extract_daily_news_features(
        news_articles=news_articles,
        corporate_disclosures=corporate_disclosures,
    )

    assert not features_df.empty
    assert len(features_df) == 2  # 2 symbols on 2026-03-30
    assert set(features_df["symbol"].tolist()) == {"RELIANCE", "TCS"}

    rel_row = features_df[features_df["symbol"] == "RELIANCE"].iloc[0]
    assert rel_row["news_count_1d"] == 2
    assert rel_row["disclosure_count_1d"] == 1
    assert rel_row["has_financial_results"] == 1
    assert rel_row["has_board_meeting"] == 0
    assert rel_row["avg_sentiment_polarity_1d"] > 0.0

    tcs_row = features_df[features_df["symbol"] == "TCS"].iloc[0]
    assert tcs_row["news_count_1d"] == 1
    assert tcs_row["has_board_meeting"] == 1
    assert tcs_row["has_financial_results"] == 0


def test_extract_daily_news_features_empty():
    assert NewsFeatureExtractor.extract_daily_news_features([]).empty
