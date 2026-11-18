"""Unit tests for AlertQualityAuditor (Phase 8 — Step 8.6)."""
from datetime import datetime, timezone
import pytest
from intelligence.correlation.quality_auditor import AlertQualityAuditor
from intelligence.correlation.alert_models import SurveillanceAlertSchema


@pytest.fixture
def auditor():
    return AlertQualityAuditor()


def test_balanced_sustainable_alert_audit(auditor):
    # Batch of 10 alerts distributed across multiple tickers and priorities
    alerts = []
    tickers = ["NSE:RELIANCE", "NSE:TCS", "NSE:INFY", "NSE:HDFCBANK", "NSE:TATAMOTORS"]
    tiers = [
        "INFORMATIONAL", "LOW", "MEDIUM", "INFORMATIONAL", "LOW",
        "HIGH", "INFORMATIONAL", "MEDIUM", "CRITICAL", "LOW"
    ]

    for idx, (ticker, tier) in enumerate(zip(tickers * 2, tiers)):
        score = 0.90 if tier == "CRITICAL" else (0.75 if tier == "HIGH" else 0.30)
        alerts.append(
            SurveillanceAlertSchema(
                alert_id=f"ALT_AUDIT_{idx:03d}",
                ticker=ticker,
                company_name=ticker.replace("NSE:", ""),
                alert_timestamp=datetime(2026, 11, 17, 10, idx, tzinfo=timezone.utc),
                priority_tier=tier,
                composite_risk_score=score,
                confidence=0.85,
                primary_risk_driver="Market Volume/Price Shock",
                temporal_relationship="COINCIDENT_REACTION",
                sla_triage_hours=8,
                requires_human_escalation=tier in ["HIGH", "CRITICAL"],
                recommended_action="Audit",
                market_snapshot={},
                risk_breakdown={},
            )
        )

    metrics = auditor.audit_alerts(alerts)

    assert metrics.total_alerts == 10
    assert metrics.actionable_alerts == 2  # 1 HIGH, 1 CRITICAL
    assert metrics.actionable_ratio == 0.20  # 20% actionable (<= 40% threshold)
    assert metrics.informational_ratio == 0.60
    assert metrics.ticker_concentration_hhi < 0.30
    assert metrics.is_operationally_sustainable


def test_monopolistic_ticker_fatigue_alert(auditor):
    # Single ticker monopolizing alerts (8 out of 10)
    alerts = []
    for idx in range(10):
        ticker = "NSE:RELIANCE" if idx < 8 else "NSE:TCS"
        alerts.append(
            SurveillanceAlertSchema(
                alert_id=f"ALT_FATIGUE_{idx:03d}",
                ticker=ticker,
                company_name="Reliance",
                alert_timestamp=datetime(2026, 11, 17, 10, idx, tzinfo=timezone.utc),
                priority_tier="CRITICAL",
                composite_risk_score=0.90,
                confidence=0.90,
                primary_risk_driver="Leak",
                temporal_relationship="PRE_ANNOUNCEMENT_LEAK",
                sla_triage_hours=2,
                requires_human_escalation=True,
                recommended_action="Forensic",
                market_snapshot={},
                risk_breakdown={},
            )
        )

    metrics = auditor.audit_alerts(alerts)

    assert metrics.top_concentrated_ticker == "NSE:RELIANCE"
    assert metrics.top_ticker_alert_percentage == 80.0
    assert metrics.ticker_concentration_hhi > 0.60
    assert not metrics.is_operationally_sustainable
    assert metrics.alert_fatigue_index > 0.60
