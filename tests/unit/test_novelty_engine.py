"""Unit tests for NewsNoveltyIntensityEngine (Phase 7 — Step 7.6)."""
from datetime import datetime, timedelta, timezone
import pytest
from intelligence.nlp.novelty_engine import NewsNoveltyIntensityEngine


@pytest.fixture
def novelty_engine():
    return NewsNoveltyIntensityEngine(
        jaccard_duplicate_threshold=0.70,
        decay_halflife_hours=6.0,
        burst_threshold_count=3
    )


def test_first_story_maximum_novelty(novelty_engine):
    t0 = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)
    res = novelty_engine.process_story(
        story_id="s1",
        ticker="TATAMOTORS",
        headline="Tata Motors announces electric truck production milestone in Pune",
        timestamp=t0,
        source="Reuters",
        content_hash="hash_s1"
    )

    assert res.is_novel
    assert res.novelty_score == 1.0
    assert res.cluster_size_24h == 1
    assert res.source_diversity_count == 1
    assert not res.is_breaking_burst


def test_exact_and_near_duplicate_detection(novelty_engine):
    t0 = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(minutes=15)

    # First story
    novelty_engine.process_story(
        story_id="s1",
        ticker="RELIANCE",
        headline="Reliance Retail to acquire FMCG brand for Rs 5,000 crore",
        timestamp=t0,
        source="PTI",
        content_hash="hash_ril_1"
    )

    # Syndicated near-duplicate on Bloomberg
    res2 = novelty_engine.process_story(
        story_id="s2",
        ticker="RELIANCE",
        headline="Reliance Retail to acquire FMCG brand for Rs 5,000 crore deal",
        timestamp=t1,
        source="Bloomberg",
        content_hash="hash_ril_2"
    )

    assert not res2.is_novel
    assert res2.novelty_score < 0.30
    assert res2.cluster_size_24h == 2
    assert res2.source_diversity_count == 2


def test_breaking_news_burst_detection(novelty_engine):
    t0 = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)

    # 3 distinct stories arriving within 2 hours
    novelty_engine.process_story("s1", "INFY", "Infosys signs $1B deal with telco", t0, "Reuters", "h1")
    novelty_engine.process_story("s2", "INFY", "Infosys raises full-year guidance", t0 + timedelta(minutes=30), "PTI", "h2")
    res3 = novelty_engine.process_story("s3", "INFY", "SEBI seeks clarification from Infosys", t0 + timedelta(hours=1), "CNBC", "h3")

    assert res3.is_breaking_burst
    assert res3.cluster_size_24h == 3
    assert res3.source_diversity_count == 3
    assert res3.decay_weighted_intensity > 2.5
