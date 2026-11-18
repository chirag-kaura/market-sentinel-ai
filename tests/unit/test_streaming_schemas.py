"""Unit tests for Streaming Event Schemas and JSON Schema Compliance."""
import json
import os
import jsonschema
import pytest

SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "streaming", "schemas")


@pytest.fixture
def news_schema():
    """Load news event JSON schema."""
    schema_path = os.path.join(SCHEMAS_DIR, "news_event_schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def corporate_schema():
    """Load corporate event JSON schema."""
    schema_path = os.path.join(SCHEMAS_DIR, "corporate_event_schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_news_event_schema_validation_valid(news_schema):
    """Test valid NewsEventMessage validation."""
    valid_payload = {
        "event_id": "8f3b2e1a-5c9d-4e2b-a123-9f8e7d6c5b4a",
        "canonical_url": "https://economictimes.indiatimes.com/stocks/tatamotors-jlr-surge",
        "title": "Tata Motors shares surge 6% on strong JLR global deliveries",
        "summary": "Tata Motors rallied following robust wholesale deliveries reported across Europe.",
        "body_text": None,
        "source_outlet": "Economic Times",
        "detected_symbols": ["TATAMOTORS"],
        "published_at_utc": "2026-11-17T04:45:30Z",
        "ingested_at_utc": "2026-11-17T04:46:10Z",
        "headline_hash": "a1b2c3d4e5f6789012345678abcdef01",
    }
    # Should not raise exception
    jsonschema.validate(instance=valid_payload, schema=news_schema)


def test_news_event_schema_validation_missing_required(news_schema):
    """Test validation failure on missing required fields."""
    invalid_payload = {
        "event_id": "8f3b2e1a-5c9d-4e2b-a123-9f8e7d6c5b4a",
        "title": "Short title",
        # Missing canonical_url, source_outlet, timestamps
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_payload, schema=news_schema)


def test_corporate_event_schema_validation_valid(corporate_schema):
    """Test valid CorporateEventMessage validation."""
    valid_payload = {
        "event_id": "4a7b9c2d-1e3f-4a5b-9c8d-7e6f5a4b3c2d",
        "symbol": "TATAMOTORS",
        "category": "FINANCIAL_RESULTS",
        "subject": "Outcome of Board Meeting for Q2 Financial Results",
        "body_text": "The Board approved unaudited quarterly results with revenue up 18%.",
        "attachment_url": "https://nsearchives.nseindia.com/corporate/TATAMOTORS_17112026.pdf",
        "published_at_utc": "2026-11-17T14:45:00Z",
        "ingested_at_utc": "2026-11-17T14:45:15Z",
        "source_provider": "SRC-NSE-CORP-ANNOUNCEMENTS",
    }
    # Should not raise exception
    jsonschema.validate(instance=valid_payload, schema=corporate_schema)


def test_corporate_event_schema_validation_invalid_symbol(corporate_schema):
    """Test corporate event schema failure on empty symbol."""
    invalid_payload = {
        "event_id": "4a7b9c2d-1e3f-4a5b-9c8d-7e6f5a4b3c2d",
        "symbol": "",  # Min length 1 required
        "category": "FINANCIAL_RESULTS",
        "subject": "Board Meeting",
        "published_at_utc": "2026-11-17T14:45:00Z",
        "ingested_at_utc": "2026-11-17T14:45:15Z",
        "source_provider": "SRC-NSE-CORP-ANNOUNCEMENTS",
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_payload, schema=corporate_schema)
