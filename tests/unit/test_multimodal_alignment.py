"""
Unit Tests for Multimodal Market-News Feature Alignment Engine
Market Sentinel AI — Phase 5: Step 5.5
"""

from datetime import date, timedelta
import pandas as pd
import pytest

from processing.features.multimodal_alignment import MultimodalFeatureAligner


@pytest.fixture
def mock_market_features():
    """Generates 5 days of mock market features for RELIANCE and TCS."""
    dates = [date(2026, 3, 30) + timedelta(days=i) for i in range(5)]
    records = []
    for sym in ["RELIANCE", "TCS"]:
        for i, dt in enumerate(dates):
            # Day 2 for RELIANCE is a sharp unannounced move: +4% return, high volume z-score
            ret = 0.04 if (sym == "RELIANCE" and i == 2) else 0.005
            vol_z = 3.2 if (sym == "RELIANCE" and i == 2) else 0.2
            records.append({
                "symbol": sym,
                "trade_date": dt,
                "close_price": 2500.0 * (1.0 + i * 0.01),
                "log_return_1d": ret,
                "volatility_20d": 0.18,
                "parkinson_volatility_20d": 0.16,
                "volume_zscore_20d": vol_z,
                "delivery_ratio": 0.52,
                "delivery_ratio_zscore_20d": 0.1,
            })
    return pd.DataFrame(records)


@pytest.fixture
def mock_news_features():
    """Generates news features covering only day 0 and day 4 (leaving days 1-3 as news vacuums)."""
    return pd.DataFrame([
        {
            "symbol": "RELIANCE",
            "trade_date": date(2026, 3, 30),  # Day 0
            "news_count_1d": 3,
            "disclosure_count_1d": 1,
            "avg_sentiment_polarity_1d": 0.65,
            "has_financial_results": 1,
            "has_board_meeting": 0,
            "has_mna_filing": 0,
            "has_compliance_action": 0,
            "news_count_3d": 3,
            "news_count_7d": 3,
            "news_velocity_zscore_30d": 1.8,
        },
        {
            "symbol": "TCS",
            "trade_date": date(2026, 4, 3),  # Day 4
            "news_count_1d": 2,
            "disclosure_count_1d": 0,
            "avg_sentiment_polarity_1d": -0.40,
            "has_financial_results": 0,
            "has_board_meeting": 0,
            "has_mna_filing": 0,
            "has_compliance_action": 0,
            "news_count_3d": 2,
            "news_count_7d": 2,
            "news_velocity_zscore_30d": 0.9,
        },
    ])


def test_align_features_structure_and_fills(mock_market_features, mock_news_features):
    aligned = MultimodalFeatureAligner.align_features(mock_market_features, mock_news_features)

    assert len(aligned) == 10  # 5 days * 2 symbols preserved
    assert "news_price_divergence" in aligned.columns
    assert "volume_news_divergence" in aligned.columns
    assert "sentiment_return_alignment" in aligned.columns
    assert "is_unbacked_market_move" in aligned.columns

    # Check that day 1 for RELIANCE (no news) has neutral filled values
    rel_day1 = aligned[(aligned["symbol"] == "RELIANCE") & (aligned["trade_date"] == date(2026, 3, 31))].iloc[0]
    assert rel_day1["news_count_1d"] == 0
    assert rel_day1["disclosure_count_1d"] == 0
    assert rel_day1["avg_sentiment_polarity_1d"] == 0.0
    assert rel_day1["has_financial_results"] == 0


def test_unbacked_market_movement_detection(mock_market_features, mock_news_features):
    aligned = MultimodalFeatureAligner.align_features(mock_market_features, mock_news_features)

    # Day 2 for RELIANCE was +4% return with 3.2 volume Z-score in a complete news vacuum
    rel_day2 = aligned[(aligned["symbol"] == "RELIANCE") & (aligned["trade_date"] == date(2026, 4, 1))].iloc[0]

    assert rel_day2["news_count_1d"] == 0
    assert rel_day2["is_unbacked_market_move"] == 1
    assert rel_day2["news_price_divergence"] == pytest.approx(0.04, abs=1e-4)
    # volume_z (3.2) - news_z (0.0) = 3.2
    assert rel_day2["volume_news_divergence"] == pytest.approx(3.2, abs=1e-2)


def test_sentiment_return_alignment_signs(mock_market_features, mock_news_features):
    aligned = MultimodalFeatureAligner.align_features(mock_market_features, mock_news_features)

    # Day 0 for RELIANCE: positive return (+0.005) and positive sentiment (+0.65) -> alignment = +1
    rel_day0 = aligned[(aligned["symbol"] == "RELIANCE") & (aligned["trade_date"] == date(2026, 3, 30))].iloc[0]
    assert rel_day0["sentiment_return_alignment"] == 1

    # Day 4 for TCS: positive return (+0.005) and negative sentiment (-0.40) -> alignment = -1 (divergence)
    tcs_day4 = aligned[(aligned["symbol"] == "TCS") & (aligned["trade_date"] == date(2026, 4, 3))].iloc[0]
    assert tcs_day4["sentiment_return_alignment"] == -1


def test_align_features_with_empty_or_no_news(mock_market_features):
    aligned_no_news = MultimodalFeatureAligner.align_features(mock_market_features, None)
    assert len(aligned_no_news) == 10
    assert (aligned_no_news["news_count_1d"] == 0).all()
    assert (aligned_no_news["avg_sentiment_polarity_1d"] == 0.0).all()

    empty_res = MultimodalFeatureAligner.align_features(pd.DataFrame())
    assert empty_res.empty
