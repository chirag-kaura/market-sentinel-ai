"""Unit tests for Surveillance Alert Schemas and Persistence Models (Phase 8 — Step 8.4)."""
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from intelligence.correlation.alert_models import SurveillanceAlertSchema, SurveillanceAlertModel
from backend.models.market import Base


@pytest.fixture
def db_session():
    # Create engine and create only the surveillance_alerts table for isolation
    engine = create_engine("sqlite:///:memory:")
    SurveillanceAlertModel.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_pydantic_alert_schema_validation():
    valid_payload = {
        "alert_id": "ALT_20261117_RELIANCE_001",
        "ticker": "NSE:RELIANCE",
        "company_name": "Reliance Industries Limited",
        "alert_timestamp": datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc),
        "priority_tier": "CRITICAL",
        "composite_risk_score": 0.89,
        "confidence": 0.88,
        "primary_risk_driver": "Pre-Announcement Timing / Leak",
        "temporal_relationship": "PRE_ANNOUNCEMENT_LEAK",
        "sla_triage_hours": 2,
        "requires_human_escalation": True,
        "recommended_action": "Immediate forensic escalation",
        "market_snapshot": {"return_zscore": 3.8, "volume_zscore": 4.5},
        "news_snapshot": {"story_id": "s1", "event": "MERGERS_ACQUISITIONS"},
        "risk_breakdown": {"market_anomaly": 0.40, "temporal_suspicion": 0.25},
        "status": "OPEN",
    }
    alert = SurveillanceAlertSchema(**valid_payload)
    assert alert.alert_id == "ALT_20261117_RELIANCE_001"
    assert alert.composite_risk_score == 0.89


def test_pydantic_alert_schema_invalid_score():
    invalid_payload = {
        "alert_id": "ALT_BAD_001",
        "ticker": "NSE:INFY",
        "company_name": "Infosys",
        "alert_timestamp": datetime.now(timezone.utc),
        "priority_tier": "HIGH",
        "composite_risk_score": 105.0,  # Invalid: score > 100.0 (FR-5.2 0-100 scale)
        "confidence": 0.80,
        "primary_risk_driver": "Shock",
        "temporal_relationship": "COINCIDENT_REACTION",
        "sla_triage_hours": 8,
        "requires_human_escalation": True,
        "recommended_action": "Review",
        "market_snapshot": {},
        "risk_breakdown": {},
    }
    with pytest.raises(ValidationError):
        SurveillanceAlertSchema(**invalid_payload)


def test_sqlalchemy_orm_persistence(db_session):
    alert_record = SurveillanceAlertModel(
        alert_id="ALT_TEST_001",
        ticker="NSE:TATAMOTORS",
        company_name="Tata Motors Limited",
        alert_timestamp=datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc),
        priority_tier="HIGH",
        composite_risk_score=0.76,
        confidence=0.82,
        primary_risk_driver="Market Volume/Price Shock",
        temporal_relationship="COINCIDENT_REACTION",
        sla_triage_hours=8,
        requires_human_escalation=1,
        recommended_action="Conduct formal compliance review",
        market_snapshot={"return_zscore": 2.8, "volume_zscore": 3.5},
        news_snapshot={"headline": "Tata Motors beats estimates"},
        risk_breakdown={"market_anomaly": 0.35, "event_relevance": 0.15},
        status="OPEN"
    )
    db_session.add(alert_record)
    db_session.commit()

    retrieved = db_session.query(SurveillanceAlertModel).filter_by(alert_id="ALT_TEST_001").first()
    assert retrieved is not None
    assert retrieved.ticker == "NSE:TATAMOTORS"
    assert retrieved.composite_risk_score == 0.76
    assert retrieved.market_snapshot["volume_zscore"] == 3.5
