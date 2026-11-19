"""
Investigation and Disposition Repository.
Handles persistent CRUD and immutable audit logging for surveillance cases in PostgreSQL / SQLite.
"""

from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from backend.models.investigation import InvestigationCaseModel, AnalystDispositionModel


class InvestigationRepository:
    """Repository handling database operations for investigation cases and analyst audit trails."""

    def __init__(self, session: Session):
        self.session = session

    def get_case(self, case_id: str) -> Optional[InvestigationCaseModel]:
        """Fetch investigation case by unique identifier."""
        return self.session.query(InvestigationCaseModel).filter_by(case_id=case_id).first()

    def list_cases(self, status: Optional[str] = None, ticker: Optional[str] = None) -> List[InvestigationCaseModel]:
        """Query investigation cases with optional filtering."""
        query = select(InvestigationCaseModel)
        if status:
            query = query.where(InvestigationCaseModel.status == status.upper())
        if ticker:
            query = query.where(InvestigationCaseModel.ticker == ticker.upper())
        query = query.order_by(desc(InvestigationCaseModel.updated_at))
        return list(self.session.scalars(query).all())

    def create_or_get_case(
        self,
        case_id: str,
        alert_id: str,
        ticker: str,
        dossier_text: Optional[str] = None,
        analyst_notes: Optional[str] = None,
        evidence_count: int = 1,
    ) -> InvestigationCaseModel:
        """Create new investigation case or return existing record."""
        case = self.get_case(case_id)
        if case:
            return case

        now = datetime.now(timezone.utc)
        case = InvestigationCaseModel(
            case_id=case_id,
            alert_id=alert_id,
            ticker=ticker.upper(),
            status="OPEN",
            analyst_notes=analyst_notes,
            dossier_text=dossier_text,
            evidence_count=evidence_count,
            created_at=now,
            updated_at=now,
        )
        self.session.add(case)
        self.session.commit()
        self.session.refresh(case)
        return case

    def update_case_status(
        self,
        case_id: str,
        new_status: str,
        analyst: str,
        rationale: Optional[str] = None,
    ) -> Optional[InvestigationCaseModel]:
        """Update case status and log immutable audit disposition."""
        case = self.get_case(case_id)
        if not case:
            return None

        case.status = new_status.upper()
        case.updated_at = datetime.now(timezone.utc)

        disposition = AnalystDispositionModel(
            id=str(uuid.uuid4()),
            case_id=case_id,
            alert_id=case.alert_id,
            analyst_username=analyst,
            action=f"STATUS_{new_status.upper()}",
            disposition_notes=rationale or f"Status transitioned to {new_status.upper()}",
            reviewed_at_utc=datetime.now(timezone.utc),
        )
        self.session.add(disposition)
        self.session.commit()
        self.session.refresh(case)
        return case

    def add_notes(
        self,
        case_id: str,
        notes: str,
        analyst: str,
    ) -> Optional[InvestigationCaseModel]:
        """Append analyst notes and record disposition entry."""
        case = self.get_case(case_id)
        if not case:
            return None

        existing_notes = case.analyst_notes or ""
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        formatted_entry = f"[{timestamp_str} - {analyst}]: {notes}"
        case.analyst_notes = f"{existing_notes}\n{formatted_entry}".strip()
        case.updated_at = datetime.now(timezone.utc)

        disposition = AnalystDispositionModel(
            id=str(uuid.uuid4()),
            case_id=case_id,
            alert_id=case.alert_id,
            analyst_username=analyst,
            action="NOTE_ADDED",
            disposition_notes=notes,
            reviewed_at_utc=datetime.now(timezone.utc),
        )
        self.session.add(disposition)
        self.session.commit()
        self.session.refresh(case)
        return case

    def escalate_case(
        self,
        case_id: str,
        analyst: str,
        rationale: str,
    ) -> Optional[InvestigationCaseModel]:
        """Escalate case to regulatory Suspicious Activity Report (SAR)."""
        return self.update_case_status(case_id, "ESCALATED_SAR", analyst, rationale)

    def dismiss_case(
        self,
        case_id: str,
        analyst: str,
        rationale: str,
    ) -> Optional[InvestigationCaseModel]:
        """Dismiss case as benign / legitimate market activity with justification."""
        return self.update_case_status(case_id, "DISMISSED", analyst, rationale)

    def get_audit_trail(self, limit: int = 100) -> List[AnalystDispositionModel]:
        """Retrieve chronological, immutable analyst action history."""
        query = select(AnalystDispositionModel).order_by(desc(AnalystDispositionModel.reviewed_at_utc)).limit(limit)
        return list(self.session.scalars(query).all())
