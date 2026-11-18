"""Unit tests for MultiDimensionalRiskScorer (Phase 8 — Step 8.2)."""
from datetime import datetime, timezone
import pytest
from intelligence.correlation.temporal_aligner import (
    CorrelationEvidencePair,
    MarketAnomalySnapshot,
    NewsEventSnapshot,
    TemporalRelationshipType,
)
from intelligence.correlation.risk_scorer import MultiDimensionalRiskScorer


@pytest.fixture
def risk_scorer():
    return MultiDimensionalRiskScorer(actionable_threshold=0.65)


def test_high_risk_pre_announcement_leak(risk_scorer):
    # Significant market movement prior to regulatory probe
    m_snap = MarketAnomalySnapshot(
        timestamp=datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc),
        ticker="RELIANCE",
        ensemble_score=0.92,
        severity_tier="CRITICAL_ALERT",
        return_zscore=3.8,
        volume_zscore=4.5,
    )
    n_snap = NewsEventSnapshot(
        story_id="news_1",
        headline="SEBI serves show-cause notice over insider trading probe",
        timestamp=datetime(2026, 11, 17, 22, 0, tzinfo=timezone.utc),
        primary_event="FRAUD_INVESTIGATION",
        sentiment_compound=-0.75,
        surveillance_relevance=0.95,
        source="SEBIPortal",
    )
    pair = CorrelationEvidencePair(
        market_snapshot=m_snap,
        news_snapshot=n_snap,
        relationship_type=TemporalRelationshipType.PRE_ANNOUNCEMENT_LEAK,
        time_delta_hours=12.0,
        temporal_proximity_weight=0.50,
        suspicion_multiplier=1.40,
    )

    res = risk_scorer.calculate_risk(pair)

    assert res.composite_risk_score >= 0.75
    assert res.is_actionable_alert
    assert res.confidence >= 0.75
    assert res.breakdown.temporal_suspicion_contribution > 0


def test_benign_post_earnings_reaction(risk_scorer):
    # Moderate market reaction following public earnings report
    m_snap = MarketAnomalySnapshot(
        timestamp=datetime(2026, 11, 17, 14, 0, tzinfo=timezone.utc),
        ticker="TATAMOTORS",
        ensemble_score=0.50,
        severity_tier="WATCHLIST",
        return_zscore=1.8,
        volume_zscore=2.0,
    )
    n_snap = NewsEventSnapshot(
        story_id="news_2",
        headline="Tata Motors Q3 net profit rises 25%",
        timestamp=datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc),
        primary_event="EARNINGS_FINANCIALS",
        sentiment_compound=0.60,
        surveillance_relevance=0.50,
        source="Reuters",
    )
    pair = CorrelationEvidencePair(
        market_snapshot=m_snap,
        news_snapshot=n_snap,
        relationship_type=TemporalRelationshipType.POST_NEWS_ABSORPTION,
        time_delta_hours=-4.0,
        temporal_proximity_weight=0.80,
        suspicion_multiplier=0.85,
    )

    res = risk_scorer.calculate_risk(pair)

    # Benign reaction should remain below actionable threshold
    assert res.composite_risk_score < 0.65
    assert not res.is_actionable_alert


def test_unexplained_critical_anomaly_penalty(risk_scorer):
    # Severe market spike with no public explanation whatsoever
    m_snap = MarketAnomalySnapshot(
        timestamp=datetime(2026, 11, 17, 11, 0, tzinfo=timezone.utc),
        ticker="INFY",
        ensemble_score=0.85,
        severity_tier="CRITICAL_ALERT",
        return_zscore=4.2,
        volume_zscore=5.0,
    )
    pair = CorrelationEvidencePair(
        market_snapshot=m_snap,
        news_snapshot=None,
        relationship_type=TemporalRelationshipType.UNEXPLAINED_ABSENCE,
        time_delta_hours=None,
        temporal_proximity_weight=0.0,
        suspicion_multiplier=1.25,
    )

    res = risk_scorer.calculate_risk(pair)

    assert res.breakdown.unexplained_penalty > 0
    assert res.composite_risk_score >= 0.65
    assert res.is_actionable_alert
