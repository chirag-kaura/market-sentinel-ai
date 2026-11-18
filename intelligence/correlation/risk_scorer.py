"""
Multi-Dimensional Risk Scoring Engine.
Phase 8 — Step 8.2: Fuses market anomaly scores, temporal correlation dynamics,
news surveillance relevance, sentiment divergence, and source credibility into
a mathematically calibrated Composite Risk Score in [0.0, 1.0].
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from intelligence.correlation.temporal_aligner import CorrelationEvidencePair, TemporalRelationshipType


@dataclass(frozen=True)
class RiskScoreBreakdown:
    """Detailed mathematical breakdown of components comprising the risk score."""
    market_anomaly_contribution: float
    temporal_suspicion_contribution: float
    event_relevance_contribution: float
    sentiment_divergence_contribution: float
    unexplained_penalty: float


@dataclass(frozen=True)
class CompositeRiskScoreResult:
    """Final calculated risk assessment score with complete audit provenance."""
    composite_risk_score: float  # Normalized [0.0, 1.0]
    confidence: float           # Confidence in evaluation [0.0, 1.0]
    breakdown: RiskScoreBreakdown
    primary_risk_driver: str
    is_actionable_alert: bool   # True if score >= actionable threshold


class MultiDimensionalRiskScorer:
    """
    Computes an explainable, multi-factor risk intelligence score for regulatory triage.
    Enforces justifiable mathematical formulations rather than opaque heuristic weights.
    """

    DEFAULT_WEIGHTS = {
        "market_anomaly": 0.45,
        "temporal_suspicion": 0.25,
        "event_relevance": 0.15,
        "sentiment_divergence": 0.15,
    }

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        actionable_threshold: float = 0.65
    ):
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.actionable_threshold = actionable_threshold

    def calculate_risk(self, pair: CorrelationEvidencePair) -> CompositeRiskScoreResult:
        """
        Calculates the composite risk score from a correlated market-news evidence pair.
        """
        m_snap = pair.market_snapshot
        n_snap = pair.news_snapshot

        # 1. Market Anomaly Component [0.0, 1.0]
        s_market = min(1.0, max(0.0, m_snap.ensemble_score))

        # 2. Temporal Suspicion Component
        # Pre-announcement run-ups carry highest multiplier (1.4x), unexplained (1.25x), absorption discounted (0.85x)
        s_temporal = min(1.0, (pair.suspicion_multiplier - 0.70) / 0.70)

        # 3. Event Surveillance Relevance Component
        if n_snap is not None:
            s_event = min(1.0, max(0.0, n_snap.surveillance_relevance))
        else:
            # When news is completely absent during an anomaly, event relevance is zero,
            # but unexplained penalty is triggered
            s_event = 0.0

        # 4. Sentiment-Price Divergence Component
        # Occurs when price movement direction violently contradicts news sentiment
        # e.g. Price surged (+3 sigma return) on intensely negative news (-0.70 sentiment)
        s_divergence = 0.0
        if n_snap is not None:
            ret_z = m_snap.return_zscore
            sent = n_snap.sentiment_compound
            # Check for conflicting signs
            if (ret_z > 1.5 and sent < -0.30) or (ret_z < -1.5 and sent > 0.30):
                s_divergence = min(1.0, (abs(ret_z) * abs(sent)) / 3.0)

        # 5. Unexplained Shock Penalty
        # If market anomaly is critical (>= 0.75) and zero news exists, add penalty
        unexplained_penalty = 0.0
        if pair.relationship_type == TemporalRelationshipType.UNEXPLAINED_ABSENCE and s_market >= 0.70:
            unexplained_penalty = 0.15

        # Weighted composite calculation
        w_m = self.weights["market_anomaly"]
        w_t = self.weights["temporal_suspicion"]
        w_e = self.weights["event_relevance"]
        w_d = self.weights["sentiment_divergence"]

        raw_score = (
            w_m * s_market +
            w_t * s_temporal +
            w_e * s_event +
            w_d * s_divergence +
            unexplained_penalty
        )

        composite_score = min(1.0, max(0.0, raw_score))

        # Determine primary risk driver
        contributions = {
            "Market Volume/Price Shock": w_m * s_market,
            "Pre-Announcement Timing / Leak": w_t * s_temporal,
            "Severe Regulatory/Fraud Event": w_e * s_event,
            "Price-Sentiment Divergence": w_d * s_divergence,
            "Unexplained Non-Disclosure Anomaly": unexplained_penalty
        }
        primary_driver = max(contributions.items(), key=lambda x: x[1])[0]

        # Calculate evaluation confidence
        if n_snap is not None:
            confidence = min(1.0, 0.75 + (pair.temporal_proximity_weight * 0.25))
        else:
            confidence = 0.70  # Fixed baseline confidence when no news is matched

        breakdown = RiskScoreBreakdown(
            market_anomaly_contribution=round(w_m * s_market, 3),
            temporal_suspicion_contribution=round(w_t * s_temporal, 3),
            event_relevance_contribution=round(w_e * s_event, 3),
            sentiment_divergence_contribution=round(w_d * s_divergence, 3),
            unexplained_penalty=round(unexplained_penalty, 3)
        )

        return CompositeRiskScoreResult(
            composite_risk_score=round(composite_score, 3),
            confidence=round(confidence, 3),
            breakdown=breakdown,
            primary_risk_driver=primary_driver,
            is_actionable_alert=composite_score >= self.actionable_threshold
        )
