"""Unit tests for Streaming Event Producers (News & Corporate Filings)."""
from datetime import datetime, timezone
import json
import os
import jsonschema
import pytest

from streaming.producers.news_event_producer import NewsEventProducer
from streaming.producers.corporate_event_producer import CorporateEventProducer

SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "streaming", "schemas")


@pytest.fixture
def news_schema():
    """Load news event JSON schema."""
    with open(os.path.join(SCHEMAS_DIR, "news_event_schema.json"), "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def corporate_schema():
    """Load corporate event JSON schema."""
    with open(os.path.join(SCHEMAS_DIR, "corporate_event_schema.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def test_news_event_producer_formatting_and_schema_compliance(news_schema):
    """Test NewsEventProducer payload construction against JSON schema."""
    producer = NewsEventProducer(mock_mode=True)

    article_raw = {
        "canonical_url": "https://economictimes.indiatimes.com/stocks/tcs-results",
        "title": "TCS reports 12% profit growth in Q2 on robust BFSI demand",
        "summary": "Tata Consultancy Services delivered double-digit revenue expansion.",
        "source_outlet": "Economic Times",
        "published_at_utc": datetime(2026, 11, 17, 8, 30, 0, tzinfo=timezone.utc),
    }

    published = producer.publish_news_event(article_raw, detected_symbols=["TCS"])

    assert len(producer.published_messages) == 1
    msg_envelope = producer.published_messages[0]
    assert msg_envelope["key"] == "TCS"  # Keyed by primary symbol

    # Assert schema compliance
    jsonschema.validate(instance=published, schema=news_schema)
    assert published["detected_symbols"] == ["TCS"]
    assert published["headline_hash"] is not None


def test_corporate_event_producer_formatting_and_schema_compliance(corporate_schema):
    """Test CorporateEventProducer payload construction against JSON schema."""
    producer = CorporateEventProducer(mock_mode=True)

    announcement_raw = {
        "symbol": "RELIANCE",
        "category": "FINANCIAL_RESULTS",
        "subject": "Unaudited Standalone and Consolidated Financial Results for Q2",
        "body_text": "The Board approved quarterly revenue of Rs 2.45 lakh crore.",
        "attachment_url": "https://nsearchives.nseindia.com/corporate/RELIANCE_Q2.pdf",
        "published_at_utc": datetime(2026, 11, 17, 13, 45, 0, tzinfo=timezone.utc),
        "source_provider": "SRC-NSE-CORP-ANNOUNCEMENTS",
    }

    published = producer.publish_corporate_event(announcement_raw)

    assert len(producer.published_messages) == 1
    msg_envelope = producer.published_messages[0]
    assert msg_envelope["key"] == "RELIANCE"  # Keyed by symbol

    # Assert schema compliance
    jsonschema.validate(instance=published, schema=corporate_schema)
    assert published["symbol"] == "RELIANCE"
    assert published["category"] == "FINANCIAL_RESULTS"
