"""
Investigations & Dossier RESTful API Endpoints.
Phase 10 — Step 10.3: Investigative case management and dossier generation.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Query, Path
from pydantic import BaseModel, Field
from backend.core.exceptions import EntityNotFoundError

router = APIRouter(prefix="/investigations", tags=["Investigations"])


class InvestigationCase(BaseModel):
    case_id: str
    alert_id: str
    ticker: str
    status: str  # OPEN, IN_PROGRESS, CLOSED, ESCALATED
    analyst_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    dossier_text: Optional[str] = None
    evidence_count: int = 0


_CASES = {
    "CASE-2026-001": InvestigationCase(
        case_id="CASE-2026-001",
        alert_id="ALT-202611-001",
        ticker="INFY",
        status="OPEN",
        analyst_notes="Under initial triage for abnormal pre-announcement trading volume.",
        created_at=datetime(2026, 11, 15, 15, 0, 0),
        updated_at=datetime(2026, 11, 15, 15, 0, 0),
        dossier_text="### Market Sentinel Surveillance Dossier\nTarget: INFY\nSeverity: CRITICAL",
        evidence_count=2,
    )
}


@router.get("", response_model=List[InvestigationCase])
def list_cases(
    status: Optional[str] = Query(None, description="Filter by status: OPEN, IN_PROGRESS, CLOSED, ESCALATED"),
    ticker: Optional[str] = Query(None, description="Filter by stock ticker symbol"),
):
    """List open and historical investigation cases."""
    results = list(_CASES.values())
    if status:
        results = [c for c in results if c.status.upper() == status.upper()]
    if ticker:
        results = [c for c in results if c.ticker.upper() == ticker.upper()]
    return results


@router.get("/{case_id}", response_model=InvestigationCase)
def get_case_detail(
    case_id: str = Path(..., description="Unique case identifier")
):
    """Retrieve full investigation workspace case and dossier."""
    if case_id not in _CASES:
        raise EntityNotFoundError(entity_name="InvestigationCase", entity_id=case_id)
    return _CASES[case_id]
