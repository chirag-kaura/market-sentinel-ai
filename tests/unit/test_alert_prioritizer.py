"""Unit tests for AlertPrioritizer (Phase 8 — Step 8.3)."""
import pytest
from intelligence.correlation.alert_prioritizer import AlertPrioritizer, AlertPriorityTier
from intelligence.correlation.risk_scorer import CompositeRiskScoreResult, RiskScoreBreakdown


@pytest.fixture
def prioritizer():
    return AlertPrioritizer()


def test_critical_alert_prioritization(prioritizer):
    risk_res = CompositeRiskScoreResult(
        composite_risk_score=0.88,
        confidence=0.85,
        breakdown=RiskScoreBreakdown(0.40, 0.25, 0.15, 0.08, 0.0),
        primary_risk_driver="Pre-Announcement Timing / Leak",
        is_actionable_alert=True
    )
    p_res = prioritizer.prioritize(risk_res)

    assert p_res.priority_tier == AlertPriorityTier.CRITICAL
    assert p_res.sla_triage_hours == 2
    assert p_res.requires_human_escalation
    assert "Immediate forensic escalation" in p_res.recommended_action


def test_high_alert_prioritization(prioritizer):
    risk_res = CompositeRiskScoreResult(
        composite_risk_score=0.72,
        confidence=0.80,
        breakdown=RiskScoreBreakdown(0.35, 0.20, 0.10, 0.07, 0.0),
        primary_risk_driver="Market Volume/Price Shock",
        is_actionable_alert=True
    )
    p_res = prioritizer.prioritize(risk_res)

    assert p_res.priority_tier == AlertPriorityTier.HIGH
    assert p_res.sla_triage_hours == 8
    assert p_res.requires_human_escalation


def test_medium_alert_prioritization(prioritizer):
    risk_res = CompositeRiskScoreResult(
        composite_risk_score=0.55,
        confidence=0.75,
        breakdown=RiskScoreBreakdown(0.25, 0.15, 0.10, 0.05, 0.0),
        primary_risk_driver="Market Volume/Price Shock",
        is_actionable_alert=False
    )
    p_res = prioritizer.prioritize(risk_res)

    assert p_res.priority_tier == AlertPriorityTier.MEDIUM
    assert p_res.sla_triage_hours == 24
    assert not p_res.requires_human_escalation


def test_informational_alert_prioritization(prioritizer):
    risk_res = CompositeRiskScoreResult(
        composite_risk_score=0.20,
        confidence=0.90,
        breakdown=RiskScoreBreakdown(0.10, 0.05, 0.05, 0.0, 0.0),
        primary_risk_driver="Market Volume/Price Shock",
        is_actionable_alert=False
    )
    p_res = prioritizer.prioritize(risk_res)

    assert p_res.priority_tier == AlertPriorityTier.INFORMATIONAL
    assert not p_res.requires_human_escalation
    assert "No action required" in p_res.recommended_action
