"""Unit tests for HistoricalSurveillanceReplayHarness (Phase 8 — Step 8.5)."""
from datetime import datetime, timedelta, timezone
import pytest
from intelligence.correlation.backtesting_harness import HistoricalSurveillanceReplayHarness
from intelligence.correlation.temporal_aligner import MarketAnomalySnapshot, NewsEventSnapshot


@pytest.fixture
def replay_harness():
    return HistoricalSurveillanceReplayHarness()


def test_historical_replay_sequence(replay_harness):
    t0 = datetime(2026, 11, 10, 10, 0, tzinfo=timezone.utc)

    # 3 chronological market anomalies
    anomalies = [
        MarketAnomalySnapshot(
            timestamp=t0,
            ticker="RELIANCE",
            ensemble_score=0.90,
            severity_tier="CRITICAL_ALERT",
            return_zscore=3.5,
            volume_zscore=4.8,
        ),
        MarketAnomalySnapshot(
            timestamp=t0 + timedelta(days=2),
            ticker="TATAMOTORS",
            ensemble_score=0.45,
            severity_tier="WATCHLIST",
            return_zscore=1.5,
            volume_zscore=1.8,
        ),
        MarketAnomalySnapshot(
            timestamp=t0 + timedelta(days=5),
            ticker="INFY",
            ensemble_score=0.75,
            severity_tier="SUSPICIOUS",
            return_zscore=-3.0,
            volume_zscore=3.2,
        ),
    ]

    # Historical news stream
    news = [
        # News arrives 18 hours after the first Reliance anomaly (leak scenario)
        NewsEventSnapshot(
            story_id="n1",
            headline="Reliance Retail acquires major FMCG entity",
            timestamp=t0 + timedelta(hours=18),
            primary_event="MERGERS_ACQUISITIONS",
            sentiment_compound=0.60,
            surveillance_relevance=0.85,
            source="NSEFiling",
        ),
        # News arrives 2 hours before the second Tata Motors anomaly (post-earnings scenario)
        NewsEventSnapshot(
            story_id="n2",
            headline="Tata Motors commercial vehicles update",
            timestamp=t0 + timedelta(days=2) - timedelta(hours=2),
            primary_event="EARNINGS_FINANCIALS",
            sentiment_compound=0.40,
            surveillance_relevance=0.50,
            source="PTI",
        ),
    ]

    alerts, summary = replay_harness.run_replay(anomalies, news)

    assert len(alerts) == 3
    assert summary.total_alerts_generated == 3
    assert summary.high_alerts_count >= 1
    assert summary.actionable_alert_ratio > 0.0

    # First alert should reflect pre-announcement timing
    first_alert = alerts[0]
    assert first_alert.ticker == "NSE:RELIANCE"
    assert first_alert.priority_tier == "HIGH"
    assert first_alert.temporal_relationship == "PRE_ANNOUNCEMENT_LEAK"

    # Second alert should be lower priority (routine post-news reaction)
    second_alert = alerts[1]
    assert second_alert.ticker == "NSE:TATAMOTORS"
    assert second_alert.priority_tier in ["LOW", "MEDIUM", "INFORMATIONAL"]

    # Third alert had no news (unexplained)
    third_alert = alerts[2]
    assert third_alert.ticker == "NSE:INFY"
    assert third_alert.temporal_relationship == "UNEXPLAINED_ABSENCE"
