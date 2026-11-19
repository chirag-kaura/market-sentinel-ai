"""
Investigations & Dossier RESTful API Endpoints.
Phase 10 — Step 10.3 / 10.5: Persistent case management, notes, status transitions,
escalation/dismissal workflows, and database-backed immutable regulatory audit trail.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Path, Body, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.core.database import get_db, init_db
from backend.core.exceptions import EntityNotFoundError, SurveillanceAPIException
from backend.core.security import get_current_user, User, UserRole, RoleChecker
from backend.repositories.investigation_repository import InvestigationRepository

router = APIRouter(prefix="/investigations", tags=["Investigations"], dependencies=[Depends(get_current_user)])


class InvestigationCaseSchema(BaseModel):
    case_id: str
    alert_id: str
    ticker: str
    status: str
    analyst_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    dossier_text: Optional[str] = None
    evidence_count: int = 0


class CreateCaseRequest(BaseModel):
    case_id: str
    alert_id: str
    ticker: str
    dossier_text: Optional[str] = None
    analyst_notes: Optional[str] = None


class CaseUpdateNotesRequest(BaseModel):
    notes: str = Field(..., min_length=1, description="Analyst notes to append")


class CaseStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Target status: OPEN, UNDER_REVIEW, ESCALATED_SAR, DISMISSED")
    rationale: Optional[str] = Field(None, description="Compliance reasoning for transition")


class CaseEscalateRequest(BaseModel):
    rationale: str = Field(..., min_length=5, description="Justification for SAR escalation")


class CaseDismissRequest(BaseModel):
    rationale: str = Field(..., min_length=5, description="Justification for alert dismissal")


class AuditDispositionSchema(BaseModel):
    case_id: str
    alert_id: str
    analyst_username: str
    action: str
    disposition_notes: str
    reviewed_at_utc: datetime


def _ensure_seed_cases(repo: InvestigationRepository):
    """Ensure baseline demonstration cases exist in the database."""
    if not repo.get_case("CASE-2026-001"):
        repo.create_or_get_case(
            case_id="CASE-2026-001",
            alert_id="ALT-202611-001",
            ticker="INFY",
            analyst_notes="Under initial triage for abnormal pre-announcement trading volume.",
            dossier_text="### Market Sentinel Surveillance Dossier\nTarget: INFY\nSeverity: CRITICAL",
            evidence_count=2,
        )


@router.get("", response_model=List[InvestigationCaseSchema])
def list_cases(
    status: Optional[str] = Query(None, description="Filter by status: OPEN, UNDER_REVIEW, ESCALATED_SAR, DISMISSED"),
    ticker: Optional[str] = Query(None, description="Filter by stock ticker symbol"),
    db: Session = Depends(get_db),
):
    """List open and historical investigation cases from PostgreSQL / SQLite."""
    init_db()
    repo = InvestigationRepository(db)
    _ensure_seed_cases(repo)
    cases = repo.list_cases(status=status, ticker=ticker)
    return [
        InvestigationCaseSchema(
            case_id=c.case_id,
            alert_id=c.alert_id,
            ticker=c.ticker,
            status=c.status,
            analyst_notes=c.analyst_notes,
            created_at=c.created_at,
            updated_at=c.updated_at,
            dossier_text=c.dossier_text,
            evidence_count=c.evidence_count,
        )
        for c in cases
    ]


@router.post("", response_model=InvestigationCaseSchema, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CreateCaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new formal investigation case from a surveillance alert."""
    init_db()
    repo = InvestigationRepository(db)
    case = repo.create_or_get_case(
        case_id=payload.case_id,
        alert_id=payload.alert_id,
        ticker=payload.ticker,
        dossier_text=payload.dossier_text,
        analyst_notes=payload.analyst_notes,
    )
    return InvestigationCaseSchema(
        case_id=case.case_id,
        alert_id=case.alert_id,
        ticker=case.ticker,
        status=case.status,
        analyst_notes=case.analyst_notes,
        created_at=case.created_at,
        updated_at=case.updated_at,
        dossier_text=case.dossier_text,
        evidence_count=case.evidence_count,
    )


@router.get("/audit/dispositions", response_model=List[AuditDispositionSchema])
def get_audit_trail(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve immutable, database-backed regulatory audit trail of all analyst dispositions."""
    init_db()
    repo = InvestigationRepository(db)
    dispositions = repo.get_audit_trail(limit=limit)
    return [
        AuditDispositionSchema(
            case_id=d.case_id,
            alert_id=d.alert_id,
            analyst_username=d.analyst_username,
            action=d.action,
            disposition_notes=d.disposition_notes,
            reviewed_at_utc=d.reviewed_at_utc,
        )
        for d in dispositions
    ]


@router.get("/{case_id}", response_model=InvestigationCaseSchema)
def get_case_detail(
    case_id: str = Path(..., description="Unique case identifier"),
    db: Session = Depends(get_db),
):
    """Retrieve full investigation workspace case and dossier."""
    init_db()
    repo = InvestigationRepository(db)
    _ensure_seed_cases(repo)
    case = repo.get_case(case_id)
    if not case:
        raise EntityNotFoundError(entity_name="InvestigationCase", entity_id=case_id)

    return InvestigationCaseSchema(
        case_id=case.case_id,
        alert_id=case.alert_id,
        ticker=case.ticker,
        status=case.status,
        analyst_notes=case.analyst_notes,
        created_at=case.created_at,
        updated_at=case.updated_at,
        dossier_text=case.dossier_text,
        evidence_count=case.evidence_count,
    )


@router.post("/{case_id}/notes", response_model=InvestigationCaseSchema)
def add_case_notes(
    case_id: str = Path(..., description="Unique case identifier"),
    payload: CaseUpdateNotesRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Append analyst findings/notes to an investigation file with audit logging."""
    init_db()
    repo = InvestigationRepository(db)
    case = repo.add_notes(case_id, notes=payload.notes, analyst=current_user.username)
    if not case:
        raise EntityNotFoundError(entity_name="InvestigationCase", entity_id=case_id)

    return InvestigationCaseSchema(
        case_id=case.case_id,
        alert_id=case.alert_id,
        ticker=case.ticker,
        status=case.status,
        analyst_notes=case.analyst_notes,
        created_at=case.created_at,
        updated_at=case.updated_at,
        dossier_text=case.dossier_text,
        evidence_count=case.evidence_count,
    )


@router.patch("/{case_id}/status", response_model=InvestigationCaseSchema)
def update_case_status(
    case_id: str = Path(..., description="Unique case identifier"),
    payload: CaseStatusUpdateRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition case workflow status (e.g. OPEN -> UNDER_REVIEW)."""
    init_db()
    repo = InvestigationRepository(db)
    case = repo.update_case_status(
        case_id=case_id,
        new_status=payload.status,
        analyst=current_user.username,
        rationale=payload.rationale,
    )
    if not case:
        raise EntityNotFoundError(entity_name="InvestigationCase", entity_id=case_id)

    return InvestigationCaseSchema(
        case_id=case.case_id,
        alert_id=case.alert_id,
        ticker=case.ticker,
        status=case.status,
        analyst_notes=case.analyst_notes,
        created_at=case.created_at,
        updated_at=case.updated_at,
        dossier_text=case.dossier_text,
        evidence_count=case.evidence_count,
    )


@router.post(
    "/{case_id}/escalate",
    response_model=InvestigationCaseSchema,
    dependencies=[Depends(RoleChecker([UserRole.COMPLIANCE_OFFICER.value, UserRole.ADMIN.value]))],
)
def escalate_case_to_sar(
    case_id: str = Path(..., description="Unique case identifier"),
    payload: CaseEscalateRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Escalate investigation to Suspicious Activity Report (SAR). Requires COMPLIANCE_OFFICER or ADMIN."""
    init_db()
    repo = InvestigationRepository(db)
    case = repo.escalate_case(case_id, analyst=current_user.username, rationale=payload.rationale)
    if not case:
        raise EntityNotFoundError(entity_name="InvestigationCase", entity_id=case_id)

    return InvestigationCaseSchema(
        case_id=case.case_id,
        alert_id=case.alert_id,
        ticker=case.ticker,
        status=case.status,
        analyst_notes=case.analyst_notes,
        created_at=case.created_at,
        updated_at=case.updated_at,
        dossier_text=case.dossier_text,
        evidence_count=case.evidence_count,
    )


@router.post(
    "/{case_id}/dismiss",
    response_model=InvestigationCaseSchema,
    dependencies=[Depends(RoleChecker([UserRole.COMPLIANCE_OFFICER.value, UserRole.ADMIN.value]))],
)
def dismiss_case_as_legitimate(
    case_id: str = Path(..., description="Unique case identifier"),
    payload: CaseDismissRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dismiss investigation with formal justification. Requires COMPLIANCE_OFFICER or ADMIN."""
    init_db()
    repo = InvestigationRepository(db)
    case = repo.dismiss_case(case_id, analyst=current_user.username, rationale=payload.rationale)
    if not case:
        raise EntityNotFoundError(entity_name="InvestigationCase", entity_id=case_id)

    return InvestigationCaseSchema(
        case_id=case.case_id,
        alert_id=case.alert_id,
        ticker=case.ticker,
        status=case.status,
        analyst_notes=case.analyst_notes,
        created_at=case.created_at,
        updated_at=case.updated_at,
        dossier_text=case.dossier_text,
        evidence_count=case.evidence_count,
    )
