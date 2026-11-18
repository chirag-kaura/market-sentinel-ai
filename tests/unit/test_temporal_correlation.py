"""Unit tests for TemporalCorrelationAligner (Phase 8 — Step 8.1)."""
from datetime import datetime, timedelta, timezone
import pytest
from intelligence.correlation.temporal_aligner import (
    TemporalCorrelationAligner,
    TemporalWindowConfig,
    TemporalRelationshipType,
    MarketAnomalySnapshot,
    NewsEventSnapshot,
)


@pytest.fixture
def aligner():
    config = TemporalWindowConfig(
        pre_event_window_hours=48.0,
        post_event_window_hours=24.0,
        coincident_threshold_hours=2.0,
        decay_halflife_hours=12.0,
    )
    return TemporalCorrelationAligner(config=config)


def test_pre_announcement_leak_detection(aligner):
    # Market anomaly happens at 10:00 AM on Nov 17
    t_market = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)
    market_snap = MarketAnomalySnapshot(
        timestamp=t_market,
        ticker="RELIANCE",
        ensemble_score=0.88,
        severity_tier="CRITICAL_ALERT",
        return_zscore=3.4,
        volume_zscore=4.8,
    )

    # Merger announcement news broke 18 hours LATER (Nov 17, 04:00 AM next day / 18h delta)
    t_news = t_market + timedelta(hours=18)
    news_snap = NewsEventSnapshot(
        story_id="news_1",
        headline="Reliance Retail announces mega acquisition of FMCG entity",
        timestamp=t_news,
        primary_event="MERGERS_ACQUISITIONS",
        sentiment_compound=0.55,
        surveillance_relevance=0.85,
        source="ExchangeFiling",
    )

    pair = aligner.align(market_snap, [news_snap])

    assert pair.relationship_type == TemporalRelationshipType.PRE_ANNOUNCEMENT_LEAK
    assert pair.time_delta_hours == 18.0
    assert pair.suspicion_multiplier > 1.20
    assert pair.temporal_proximity_weight > 0.0


def test_coincident_market_reaction(aligner):
    t_market = datetime(2026, 11, 17, 14, 0, tzinfo=timezone.utc)
    market_snap = MarketAnomalySnapshot(
        timestamp=t_market,
        ticker="TATAMOTORS",
        ensemble_score=0.72,
        severity_tier="SUSPICIOUS",
        return_zscore=2.8,
        volume_zscore=3.1,
    )

    # News arrived 30 minutes before market spike
    t_news = t_market - timedelta(minutes=30)
    news_snap = NewsEventSnapshot(
        story_id="news_2",
        headline="Tata Motors Q3 net profit surges 25%",
        timestamp=t_news,
        primary_event="EARNINGS_FINANCIALS",
        sentiment_compound=0.65,
        surveillance_relevance=0.60,
        source="Reuters",
    )

    pair = aligner.align(market_snap, [news_snap])

    assert pair.relationship_type == TemporalRelationshipType.COINCIDENT_REACTION
    assert pair.suspicion_multiplier == 1.0
    assert pair.temporal_proximity_weight > 0.90


def test_post_news_absorption(aligner):
    t_market = datetime(2026, 11, 17, 16, 0, tzinfo=timezone.utc)
    market_snap = MarketAnomalySnapshot(
        timestamp=t_market,
        ticker="INFY",
        ensemble_score=0.68,
        severity_tier="SUSPICIOUS",
        return_zscore=-2.5,
        volume_zscore=2.2,
    )

    # News was published 10 hours prior to the market move
    t_news = t_market - timedelta(hours=10)
    news_snap = NewsEventSnapshot(
        story_id="news_3",
        headline="Infosys faces client billing adjustments in European banking account",
        timestamp=t_news,
        primary_event="CONTRACT_ORDER_WIN",
        sentiment_compound=-0.40,
        surveillance_relevance=0.50,
        source="Livemint",
    )

    pair = aligner.align(market_snap, [news_snap])

    assert pair.relationship_type == TemporalRelationshipType.POST_NEWS_ABSORPTION
    assert pair.suspicion_multiplier < 1.0


def test_unexplained_absence_of_news(aligner):
    t_market = datetime(2026, 11, 17, 11, 30, tzinfo=timezone.utc)
    market_snap = MarketAnomalySnapshot(
        timestamp=t_market,
        ticker="SBIN",
        ensemble_score=0.91,
        severity_tier="CRITICAL_ALERT",
        return_zscore=4.5,
        volume_zscore=5.2,
    )

    # Empty candidate news list
    pair = aligner.align(market_snap, [])

    assert pair.relationship_type == TemporalRelationshipType.UNEXPLAINED_ABSENCE
    assert pair.news_snapshot is None
    assert pair.time_delta_hours is None
    assert pair.suspicion_multiplier > 1.20
