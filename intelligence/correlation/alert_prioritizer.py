"""
Alert Prioritization and Tiering Classification Engine.
Phase 8 — Step 8.3: Categorizes composite risk scores into actionable surveillance tiers
(INFORMATIONAL, LOW, MEDIUM, HIGH, CRITICAL) and generates investigation workflows.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple
from intelligence.correlation.risk_scorer import CompositeRiskScoreResult


class AlertPriorityTier(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"  # Score < 0.35: Routine market movements, no action required
    LOW = "LOW"                      # 0.35 <= Score < 0.50: Minor deviation, passive log
    MEDIUM = "MEDIUM"                # 0.50 <= Score < 0.65: Watchlist addition, automated tracking
    HIGH = "HIGH"                    # 0.65 <= Score < 0.85: Actionable surveillance alert, analyst review recommended
    CRITICAL = "CRITICAL"            # Score >= 0.85: Severe multi-factor anomaly, immediate investigative triage required


@dataclass(frozen=True)
class AlertPrioritizationResult:
    """Prioritized alert classification with workflow urgency guidance."""
    priority_tier: AlertPriorityTier
    composite_risk_score: float
    confidence: float
    sla_triage_hours: int           # Maximum SLA hours for compliance team review
    requires_human_escalation: bool # True for HIGH and CRITICAL alerts
    recommended_action: str
    primary_risk_driver: str


class AlertPrioritizer:
    """
    Classifies risk scores into regulatory compliance tiers with deterministic SLAs.
    Guarantees consistent, explainable alert prioritization to prevent surveillance fatigue.
    """

    # Configurable priority boundaries
    TIER_BOUNDARIES = {
        AlertPriorityTier.CRITICAL: 0.85,
        AlertPriorityTier.HIGH: 0.65,
        AlertPriorityTier.MEDIUM: 0.50,
        AlertPriorityTier.LOW: 0.35,
    }

    # Regulatory response SLA in hours
    SLA_HOURS = {
        AlertPriorityTier.CRITICAL: 2,    # 2 hours for immediate triage
        AlertPriorityTier.HIGH: 8,        # Same trading day
        AlertPriorityTier.MEDIUM: 24,     # Next trading day
        AlertPriorityTier.LOW: 72,        # Routine periodic audit
        AlertPriorityTier.INFORMATIONAL: 168 # Weekly archive
    }

    RECOMMENDED_ACTIONS = {
        AlertPriorityTier.CRITICAL: "Immediate forensic escalation: Freeze audit logs, query counterparty order books, and cross-reference insider trading registries.",
        AlertPriorityTier.HIGH: "Conduct formal compliance review: Verify disclosure timestamps and examine broker-dealer concentration.",
        AlertPriorityTier.MEDIUM: "Add symbol to surveillance watchlist and monitor volatility over the next 3 trading sessions.",
        AlertPriorityTier.LOW: "Passive observation: Archive signal and maintain statistical baseline tracking.",
        AlertPriorityTier.INFORMATIONAL: "No action required: Routine price-volume behavior within standard statistical bounds."
    }

    def prioritize(self, risk_result: CompositeRiskScoreResult) -> AlertPrioritizationResult:
        """Assigns an alert priority tier, review SLA, and action recommendation."""
        score = risk_result.composite_risk_score
        norm_score = score / 100.0 if score > 1.0 else score

        if norm_score >= self.TIER_BOUNDARIES[AlertPriorityTier.CRITICAL]:
            tier = AlertPriorityTier.CRITICAL
        elif norm_score >= self.TIER_BOUNDARIES[AlertPriorityTier.HIGH]:
            tier = AlertPriorityTier.HIGH
        elif norm_score >= self.TIER_BOUNDARIES[AlertPriorityTier.MEDIUM]:
            tier = AlertPriorityTier.MEDIUM
        elif norm_score >= self.TIER_BOUNDARIES[AlertPriorityTier.LOW]:
            tier = AlertPriorityTier.LOW
        else:
            tier = AlertPriorityTier.INFORMATIONAL

        requires_escalation = tier in [AlertPriorityTier.HIGH, AlertPriorityTier.CRITICAL]
        sla = self.SLA_HOURS[tier]
        action = self.RECOMMENDED_ACTIONS[tier]

        return AlertPrioritizationResult(
            priority_tier=tier,
            composite_risk_score=score,
            confidence=risk_result.confidence,
            sla_triage_hours=sla,
            requires_human_escalation=requires_escalation,
            recommended_action=action,
            primary_risk_driver=risk_result.primary_risk_driver
        )
