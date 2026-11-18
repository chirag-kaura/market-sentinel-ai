"""Unit tests for Resilient Streaming Event Consumers and DLQ Routing."""
from datetime import datetime, timezone
import json
import os
import pytest

from streaming.consumers.news_event_consumer import NewsEventConsumer
from streaming.consumers.corporate_event_consumer import CorporateEventConsumer


def test_news_event_consumer_valid_processing(tmp_path):
    """Test valid NewsEventMessage ingestion, schema verification, and offset commit."""
    dlq_file = str(tmp_path / "test_dlq.jsonl")
    consumer = NewsEventConsumer(dlq_file=dlq_file, mock_mode=True)

    valid_message = {
        "event_id": "8f3b2e1a-5c9d-4e2b-a123-9f8e7d6c5b4a",
        "canonical_url": "https://economictimes.indiatimes.com/stocks/tatamotors-jlr-surge",
        "title": "Tata Motors shares surge 6% on strong JLR global deliveries",
        "summary": "Tata Motors rallied following robust wholesale deliveries.",
        "body_text": None,
        "source_outlet": "Economic Times",
        "detected_symbols": ["TATAMOTORS"],
        "published_at_utc": "2026-11-17T04:45:30Z",
        "ingested_at_utc": "2026-11-17T04:46:10Z",
        "headline_hash": "a1b2c3d4e5f6789012345678abcdef01",
    }

    processed = consumer.process_message(valid_message)

    assert processed is not None
    assert len(consumer.processed_events) == 1
    assert consumer.processed_events[0]["event_id"] == "8f3b2e1a-5c9d-4e2b-a123-9f8e7d6c5b4a"
    assert not os.path.exists(dlq_file)  # Zero DLQ routing on valid payload


def test_news_event_consumer_dlq_quarantine_on_poison_pill(tmp_path):
    """Test quarantine DLQ routing when encountering a malformed poison-pill payload."""
    dlq_file = str(tmp_path / "test_dlq.jsonl")
    consumer = NewsEventConsumer(dlq_file=dlq_file, mock_mode=True)

    # Malformed payload: missing required fields (canonical_url, source_outlet, timestamps)
    corrupted_message = {
        "event_id": "corrupted-123",
        "title": "Short title",
    }

    processed = consumer.process_message(corrupted_message)

    assert processed is None
    assert len(consumer.processed_events) == 0
    assert os.path.exists(dlq_file)

    # Verify DLQ payload structure
    with open(dlq_file, "r", encoding="utf-8") as f:
        dlq_records = [json.loads(line) for line in f]

    assert len(dlq_records) == 1
    assert dlq_records[0]["topic"] == "news.events.raw"
    assert "Schema validation failed" in dlq_records[0]["error_message"]


def test_corporate_event_consumer_valid_and_dlq(tmp_path):
    """Test CorporateEventConsumer processing and DLQ isolation."""
    dlq_file = str(tmp_path / "test_dlq.jsonl")
    consumer = CorporateEventConsumer(dlq_file=dlq_file, mock_mode=True)

    valid_corp = {
        "event_id": "4a7b9c2d-1e3f-4a5b-9c8d-7e6f5a4b3c2d",
        "symbol": "INFY",
        "category": "FINANCIAL_RESULTS",
        "subject": "Infosys quarterly revenue beats analyst estimates",
        "body_text": "Infosys reported solid revenue growth.",
        "attachment_url": "https://nsearchives.nseindia.com/corporate/INFY_Q2.pdf",
        "published_at_utc": "2026-11-17T11:30:00Z",
        "ingested_at_utc": "2026-11-17T11:30:15Z",
        "source_provider": "SRC-NSE-CORP-ANNOUNCEMENTS",
    }

    processed = consumer.process_message(valid_corp)
    assert processed is not None
    assert len(consumer.processed_events) == 1

    # Corrupted: empty symbol
    corrupted_corp = {
        "event_id": "bad-corp-1",
        "symbol": "",
        "category": "FINANCIAL_RESULTS",
        "subject": "Filing",
        "published_at_utc": "2026-11-17T11:30:00Z",
        "ingested_at_utc": "2026-11-17T11:30:15Z",
        "source_provider": "SRC-NSE-CORP-ANNOUNCEMENTS",
    }
    processed_bad = consumer.process_message(corrupted_corp)
    assert processed_bad is None
    assert os.path.exists(dlq_file)
