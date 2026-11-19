"""
SQLAlchemy ORM models for investigation cases and analyst audit dispositions.
Phase 10 — Step 10.3 / Step 10.5: Persistent case management and regulatory audit trail.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.models.market import Base


class InvestigationCaseModel(Base):
    """SQLAlchemy model for persistent surveillance case files."""
    __tablename__ = "investigation_cases"

    case_id = Column(String(64), primary_key=True, index=True)
    alert_id = Column(String(64), nullable=False, index=True)
    ticker = Column(String(32), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="OPEN", index=True)
    analyst_notes = Column(Text, nullable=True)
    assigned_analyst = Column(String(64), nullable=True)
    dossier_text = Column(Text, nullable=True)
    evidence_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    dispositions = relationship("AnalystDispositionModel", back_populates="case_ref", cascade="all, delete-orphan")


class AnalystDispositionModel(Base):
    """SQLAlchemy model for immutable regulatory compliance audit trail."""
    __tablename__ = "analyst_dispositions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(64), ForeignKey("investigation_cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    alert_id = Column(String(64), nullable=False, index=True)
    analyst_username = Column(String(64), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # NOTE_ADDED, STATUS_CHANGED, ESCALATED_TO_SAR, DISMISSED
    disposition_notes = Column(Text, nullable=False)
    reviewed_at_utc = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    case_ref = relationship("InvestigationCaseModel", back_populates="dispositions")
