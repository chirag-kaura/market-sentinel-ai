"""
Standardized Surveillance Alert Schemas and Persistence Models.
Phase 8 — Step 8.4: Pydantic schemas and SQLAlchemy ORM models establishing
auditable, immutable persistence for surveillance alerts in PostgreSQL.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from backend.models.market import Base


class SurveillanceAlertSchema(BaseModel):
    """Pydantic validation schema for surveillance alert payload."""
    alert_id: str = Field(..., description="Unique deterministic or UUID alert identifier")
    ticker: str = Field(..., description="Canonical stock symbol e.g. NSE:RELIANCE")
    company_name: str = Field(..., description="Full legal name of the entity")
    alert_timestamp: datetime = Field(..., description="Timestamp of the triggering event")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    priority_tier: str = Field(..., description="AlertPriorityTier: INFORMATIONAL, LOW, MEDIUM, HIGH, CRITICAL")
    composite_risk_score: float = Field(..., ge=0.0, le=100.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    primary_risk_driver: str
    temporal_relationship: str
    sla_triage_hours: int
    requires_human_escalation: bool
    recommended_action: str
    market_snapshot: Dict[str, Any]
    news_snapshot: Optional[Dict[str, Any]] = None
    risk_breakdown: Dict[str, float]
    status: str = Field(default="OPEN", description="Investigation status: OPEN, UNDER_REVIEW, DISMISSED, ESCALATED")


class SurveillanceAlertModel(Base):
    """SQLAlchemy ORM model for surveillance alerts stored in PostgreSQL."""
    __tablename__ = "surveillance_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(64), unique=True, nullable=False, index=True)
    ticker = Column(String(32), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    alert_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    priority_tier = Column(String(32), nullable=False, index=True)
    composite_risk_score = Column(Float, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    primary_risk_driver = Column(String(128), nullable=False)
    temporal_relationship = Column(String(64), nullable=False)
    sla_triage_hours = Column(Integer, nullable=False)
    requires_human_escalation = Column(Integer, nullable=False)  # Stored as 0 or 1 for universal SQL compatibility
    recommended_action = Column(Text, nullable=False)
    # Using JSON type for cross-dialect compatibility (PostgreSQL JSONB / SQLite JSON)
    market_snapshot = Column(JSON, nullable=False)
    news_snapshot = Column(JSON, nullable=True)
    risk_breakdown = Column(JSON, nullable=False)
    status = Column(String(32), default="OPEN", nullable=False, index=True)

    __table_args__ = (
        Index("idx_alert_ticker_time", "ticker", "alert_timestamp"),
        Index("idx_alert_tier_status", "priority_tier", "status"),
    )
