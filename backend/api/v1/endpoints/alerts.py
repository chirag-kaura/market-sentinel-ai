"""
Alerts RESTful API Endpoints.
Phase 10 — Step 10.3: Surveillance alert query, filtration, and detail retrieval
backed by the master surveillance catalog.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Path
from pydantic import BaseModel, Field
from backend.core.exceptions import EntityNotFoundError
from backend.services.surveillance_catalog import (
    get_catalog_alerts,
    get_catalog_alert_by_id,
    LiveAlertItem,
)

router = APIRouter(prefix="/alerts", tags=["Alerts"])


class AlertSummary(BaseModel):
    alert_id: str
    ticker: str
    event_timestamp: datetime
    composite_risk_score: float
    priority_level: str
    anomaly_category: str
    summary_explanation: str


class AlertDetail(AlertSummary):
    model_version: str
    abnormal_return: float
    volume_ratio: float
    sentiment_score: float
    novelty_score: float
    citations: List[str] = Field(default_factory=list)


@router.get("", response_model=List[AlertSummary])
def list_alerts(
    ticker: Optional[str] = Query(None, description="Filter by stock ticker symbol"),
    priority: Optional[str] = Query(None, description="Filter by priority level (CRITICAL, HIGH, MEDIUM, LOW)"),
    min_score: float = Query(0.0, ge=0.0, le=100.0, description="Minimum risk score"),
    limit: int = Query(50, ge=1, le=500, description="Max alerts to return"),
):
    """List filtered surveillance risk alerts."""
    results = get_catalog_alerts()

    if ticker:
        results = [a for a in results if a.ticker.upper() == ticker.upper()]
    if priority:
        results = [a for a in results if a.priority_level.upper() == priority.upper()]
    results = [a for a in results if a.composite_risk_score >= min_score]

    return results[:limit]


@router.get("/{alert_id}", response_model=AlertDetail)
def get_alert_detail(
    alert_id: str = Path(..., description="Unique alert identifier")
):
    """Retrieve full audit details for a specific surveillance alert."""
    alert = get_catalog_alert_by_id(alert_id)
    if alert:
        return alert

    raise EntityNotFoundError(entity_name="Alert", entity_id=alert_id)
