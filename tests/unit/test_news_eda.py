"""
Unit Tests for News & Corporate Disclosures EDA Engine
Market Sentinel AI — Phase 5: Step 5.3
"""

from datetime import datetime, timedelta, timezone
import pytest

from processing.eda.news_eda import NewsDisclosureEDAProfiler, NewsDistributionProfile


@pytest.fixture
def sample_news_corpus():
    base_time = datetime(2026, 3, 30, 4, 30, 0, tzinfo=timezone.utc)  # Monday 10:00 IST (Market Hours)
    articles = [
        {
            "title": "Reliance Q4 profit jumps 15 percent on strong retail growth",
            "summary": "Reliance Industries reported strong earnings driven by consumer business.",
            "published_at_utc": base_time.isoformat(),
            "detected_symbols": ["RELIANCE"],
        },
        {
            "title": "TCS bags mega financial cloud contract in Europe",
            "summary": "Tata Consultancy Services announced a multi-year IT partnership.",
            "published_at_utc": (base_time + timedelta(minutes=15)).isoformat(),
            "detected_symbols": ["TCS"],
        },
        {
            "title": "Infosys and Reliance collaborate on enterprise green hydrogen IT",
            "summary": "Joint venture announced to streamline green energy supply chains.",
            "published_at_utc": (base_time + timedelta(minutes=45)).isoformat(),
            "detected_symbols": ["INFY", "RELIANCE"],
        },
        # Weekend article (Saturday 2026-04-04 12:00 UTC)
        {
            "title": "HDFC Bank weekly analyst wrap and sector outlook",
            "summary": "Banking analysts project resilient net interest margins.",
            "published_at_utc": datetime(2026, 4, 4, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
            "detected_symbols": ["HDFCBANK"],
        },
    ]
    return articles


def test_is_market_hours_utc():
    # Monday 05:00 UTC (10:30 IST) -> Market hours
    dt_mkt = datetime(2026, 3, 30, 5, 0, 0, tzinfo=timezone.utc)
    assert NewsDisclosureEDAProfiler.is_market_hours_utc(dt_mkt) is True

    # Monday 02:00 UTC (07:30 IST) -> Pre-market
    dt_pre = datetime(2026, 3, 30, 2, 0, 0, tzinfo=timezone.utc)
    assert NewsDisclosureEDAProfiler.is_market_hours_utc(dt_pre) is False

    # Saturday 05:00 UTC -> Weekend
    dt_sat = datetime(2026, 4, 4, 5, 0, 0, tzinfo=timezone.utc)
    assert NewsDisclosureEDAProfiler.is_market_hours_utc(dt_sat) is False


def test_profile_news_corpus(sample_news_corpus):
    profile = NewsDisclosureEDAProfiler.profile_news_corpus(sample_news_corpus)
    assert isinstance(profile, NewsDistributionProfile)
    assert profile.total_articles == 4
    assert profile.unique_symbols_covered == 4
    # RELIANCE has 2 mentions
    assert profile.top_covered_symbols["RELIANCE"] == 2
    # 3 out of 4 articles are during market hours
    assert profile.market_hours_article_pct == 0.75
    # 1 out of 4 articles is on weekend
    assert profile.weekend_article_pct == 0.25
    assert profile.avg_headline_words > 5.0
    assert profile.avg_inter_arrival_minutes > 0.0


def test_profile_corporate_disclosures():
    disclosures = [
        {"symbol": "RELIANCE", "announcement_type": "Financial Results"},
        {"symbol": "RELIANCE", "announcement_type": "Board Meeting"},
        {"symbol": "TCS", "announcement_type": "Dividend"},
        {"symbol": "INFY", "announcement_type": "Financial Results"},
    ]
    summary = NewsDisclosureEDAProfiler.profile_corporate_disclosures(disclosures)
    assert summary["total_filings"] == 4
    assert summary["categories"]["Financial Results"] == 2
    assert summary["categories"]["Board Meeting"] == 1
    assert summary["top_symbols"]["RELIANCE"] == 2


def test_profile_empty_news_corpus():
    profile = NewsDisclosureEDAProfiler.profile_news_corpus([])
    assert profile.total_articles == 0
    assert profile.unique_symbols_covered == 0
    assert profile.avg_inter_arrival_minutes == 0.0
