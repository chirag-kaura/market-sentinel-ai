"""Surveillance Risk Alert Repository.

Handles database querying and persistence for risk alerts backed by PostgreSQL/SQLite.
"""
from datetime import date, datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from backend.models.market import RiskAlertModel
from backend.services.surveillance_catalog import SURVEILLANCE_CATALOG


class AlertRepository:
    """Repository handling database operations for risk alerts."""

    def __init__(self, session: Session):
        self.session = session

    def seed_initial_alerts_if_empty(self) -> int:
        """Seed the authentic surveillance catalog into risk_alerts if empty."""
        count = self.session.query(RiskAlertModel).count()
        if count > 0:
            return 0

        inserted = 0
        for item in SURVEILLANCE_CATALOG:
            alert = RiskAlertModel(
                id=item.alert_id,
                symbol=item.ticker,
                alert_date=item.event_timestamp.date() if hasattr(item.event_timestamp, "date") else date.today(),
                risk_score=item.composite_risk_score,
                priority_tier=item.priority_level,
                alert_category=item.anomaly_category,
                summary_explanation=item.summary_explanation,
                abnormal_return=item.abnormal_return,
                volume_ratio=item.volume_ratio,
                sentiment_score=item.sentiment_score,
                novelty_score=item.novelty_score,
                has_matching_news=bool(item.citations),
                dossier_status="GENERATED",
                review_status="UNREVIEWED",
                citations=item.citations,
                model_version=item.model_version,
                created_at_utc=item.event_timestamp if item.event_timestamp.tzinfo else item.event_timestamp.replace(tzinfo=timezone.utc),
            )
            self.session.add(alert)
            inserted += 1

        self.session.commit()
        return inserted

    def list_alerts(
        self,
        symbol: Optional[str] = None,
        priority: Optional[str] = None,
        min_score: float = 0.0,
        limit: int = 50,
    ) -> List[RiskAlertModel]:
        """Query alerts matching criteria."""
        self.seed_initial_alerts_if_empty()

        query = select(RiskAlertModel)
        if symbol:
            query = query.where(RiskAlertModel.symbol == symbol.upper())
        if priority:
            query = query.where(RiskAlertModel.priority_tier == priority.upper())
        if min_score > 0.0:
            query = query.where(RiskAlertModel.risk_score >= min_score)

        query = query.order_by(desc(RiskAlertModel.risk_score), desc(RiskAlertModel.created_at_utc)).limit(limit)
        return list(self.session.scalars(query).all())

    def get_alert_by_id(self, alert_id: str) -> Optional[RiskAlertModel]:
        """Fetch alert detail by ID."""
        self.seed_initial_alerts_if_empty()
        return self.session.query(RiskAlertModel).filter(RiskAlertModel.id == alert_id).first()

    def upsert_alert(self, alert_data: Dict) -> RiskAlertModel:
        """Insert or update a risk alert record."""
        alert_id = alert_data.get("id") or alert_data.get("alert_id")
        existing = None
        if alert_id:
            existing = self.session.query(RiskAlertModel).filter(RiskAlertModel.id == alert_id).first()

        if existing:
            for k, v in alert_data.items():
                if hasattr(existing, k):
                    setattr(existing, k, v)
            self.session.commit()
            self.session.refresh(existing)
            return existing

        new_alert = RiskAlertModel(
            id=alert_id,
            symbol=alert_data["symbol"],
            alert_date=alert_data.get("alert_date", date.today()),
            risk_score=alert_data["risk_score"],
            priority_tier=alert_data["priority_tier"],
            alert_category=alert_data.get("alert_category", "ANOMALY"),
            summary_explanation=alert_data.get("summary_explanation", ""),
            abnormal_return=alert_data.get("abnormal_return"),
            volume_ratio=alert_data.get("volume_ratio"),
            sentiment_score=alert_data.get("sentiment_score"),
            novelty_score=alert_data.get("novelty_score"),
            has_matching_news=alert_data.get("has_matching_news", False),
            dossier_status=alert_data.get("dossier_status", "PENDING"),
            review_status=alert_data.get("review_status", "UNREVIEWED"),
            citations=alert_data.get("citations", []),
            model_version=alert_data.get("model_version", "1.0.0"),
        )
        self.session.add(new_alert)
        self.session.commit()
        self.session.refresh(new_alert)
        return new_alert
