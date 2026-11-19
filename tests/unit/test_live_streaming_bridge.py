"""Unit tests for the live Redpanda streaming bridge and relational sink persistence."""

from datetime import date, datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import init_db
from backend.models.market import (
    CorporateAnnouncementModel,
    NewsArticleModel,
    SymbolMasterModel,
)
from streaming.consumers.corporate_event_consumer import CorporateEventConsumer
from streaming.consumers.news_event_consumer import NewsEventConsumer
from streaming.live_bridge import detect_symbols_in_text, normalize_alert_payload
from streaming.producers.corporate_event_producer import CorporateEventProducer
from streaming.producers.news_event_producer import NewsEventProducer
from streaming.sink_writer import StreamingSinkWriter


def test_default_bootstrap_servers_and_env_override(monkeypatch, tmp_path):
    """Verify producers and consumers default to localhost:9092 and honor KAFKA_BOOTSTRAP_SERVERS."""
    monkeypatch.delenv("KAFKA_BOOTSTRAP_SERVERS", raising=False)
    dlq_path = str(tmp_path / "dlq.jsonl")

    assert NewsEventProducer(mock_mode=True).bootstrap_servers == "localhost:9092"
    assert CorporateEventProducer(mock_mode=True).bootstrap_servers == "localhost:9092"
    assert NewsEventConsumer(dlq_file=dlq_path, mock_mode=True).bootstrap_servers == "localhost:9092"
    assert CorporateEventConsumer(dlq_file=dlq_path, mock_mode=True).bootstrap_servers == "localhost:9092"

    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:29092")
    assert NewsEventProducer(mock_mode=True).bootstrap_servers == "redpanda:29092"
    assert CorporateEventProducer(mock_mode=True).bootstrap_servers == "redpanda:29092"
    assert NewsEventConsumer(dlq_file=dlq_path, mock_mode=True).bootstrap_servers == "redpanda:29092"
    assert CorporateEventConsumer(dlq_file=dlq_path, mock_mode=True).bootstrap_servers == "redpanda:29092"


def test_sink_writer_idempotent_relational_persistence(tmp_path):
    """Verify StreamingSinkWriter persists news and corporate filings idempotently via SQLAlchemy."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    init_db(engine)
    SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    seed_session = SessionFactory()
    seed_session.add(
        SymbolMasterModel(
            symbol="RELIANCE",
            company_name="Reliance Industries Limited",
            isin="INE002A01018",
            sector="Energy",
            industry="Oil & Gas",
            exchange="NSE",
            series="EQ",
            listing_date=date(1977, 11, 29),
            market_cap_tier="LARGE_CAP",
            is_active=True,
            aliases=["RELIANCE.NS"],
        )
    )
    seed_session.commit()
    seed_session.close()

    writer = StreamingSinkWriter(
        parquet_base_dir=str(tmp_path / "streaming_parquet"),
        buffer_size=50,
        db_session_factory=SessionFactory,
    )

    news_record = {
        "event_id": "11111111-1111-4111-8111-111111111111",
        "canonical_url": "https://economictimes.indiatimes.com/reliance-test",
        "title": "Reliance Industries announces quarterly energy update",
        "summary": "Authentic test record for idempotent relational sink persistence.",
        "source_outlet": "Economic Times",
        "detected_symbols": ["RELIANCE"],
        "published_at_utc": datetime(2026, 11, 19, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
        "ingested_at_utc": datetime(2026, 11, 19, 10, 1, 0, tzinfo=timezone.utc).isoformat(),
        "headline_hash": "abc123def456abc123def456abc123de",
    }
    corp_valid = {
        "event_id": "22222222-2222-4222-8222-222222222222",
        "symbol": "RELIANCE",
        "category": "FINANCIAL_RESULTS",
        "subject": "Reliance Industries Board Meeting Outcome",
        "body_text": "Approved financial statements.",
        "attachment_url": "https://nsearchives.nseindia.com/corporate/REL.pdf",
        "published_at_utc": "2026-11-19T12:00:00Z",
        "ingested_at_utc": "2026-11-19T12:01:00Z",
        "source_provider": "SRC-GOOGLE-NEWS-NSE-CORP",
    }
    corp_unknown_symbol = {
        "event_id": "33333333-3333-4333-8333-333333333333",
        "symbol": "UNKNOWN_CORP",
        "category": "CORPORATE_UPDATE",
        "subject": "Unknown company event should skip safely",
        "published_at_utc": "2026-11-19T12:00:00Z",
        "ingested_at_utc": "2026-11-19T12:01:00Z",
        "source_provider": "SRC-GOOGLE-NEWS-NSE-CORP",
    }

    writer.append_event("news", news_record)
    writer.append_event("corporate", corp_valid)
    writer.append_event("corporate", corp_unknown_symbol)
    writer.flush()

    # Replay the exact same records -> relational DB counts must remain deduplicated at 1
    writer.append_event("news", news_record)
    writer.append_event("corporate", corp_valid)
    writer.flush()

    verify_session = SessionFactory()
    try:
        assert verify_session.query(NewsArticleModel).count() == 1
        assert verify_session.query(CorporateAnnouncementModel).count() == 1
        saved_corp = verify_session.query(CorporateAnnouncementModel).first()
        assert saved_corp.symbol == "RELIANCE"
    finally:
        verify_session.close()


def test_normalize_alert_payload_formats_and_symbol_detection():
    """Verify alert normalization across manual and DB payloads plus ticker matching."""
    manual_alert = {
        "alert_id": "ALT-20261102-RELI",
        "symbol": "RELIANCE",
        "priority": "critical",
        "risk_score": 88.5,
        "summary": "Unusual volume spike observed.",
    }
    norm_manual = normalize_alert_payload(manual_alert)
    assert norm_manual["event_id"] == "ALT-20261102-RELI"
    assert norm_manual["ticker"] == "RELIANCE"
    assert norm_manual["priority"] == "CRITICAL"
    assert norm_manual["composite_risk_score"] == 88.5
    assert norm_manual["feed_source"] == "REDPANDA_LIVE"

    db_alert = {
        "id": "ALT-20261118-INFY",
        "symbol": "INFY",
        "alert_date": "2026-11-18",
        "risk_score": 76.2,
        "priority_tier": "HIGH",
        "alert_category": "VOLATILITY_BAND_BREACH",
        "summary_explanation": "EWMA envelope exceeded.",
    }
    norm_db = normalize_alert_payload(db_alert)
    assert norm_db["event_id"] == "ALT-20261118-INFY"
    assert norm_db["ticker"] == "INFY"
    assert norm_db["priority"] == "HIGH"
    assert norm_db["anomaly_type"] == "VOLATILITY_BAND_BREACH"
    assert norm_db["composite_risk_score"] == 76.2

    detected = detect_symbols_in_text(
        "Infosys and Reliance Industries lead NIFTY gains; Q3 results ahead",
        ["RELIANCE", "INFY", "LT"],
    )
    assert "RELIANCE" in detected
    assert "INFY" in detected
    assert "LT" not in detected  # Must not match substring inside 'results'
