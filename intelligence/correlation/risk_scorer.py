"""Multi‑Dimensional Risk Scoring Engine – BRD‑compliant implementation (Phase 8, Step 8.2).

Aligns with FR-5.2 and FR-5.3:
- Exposes **five** BRD‑specified factors: AnomalyScore, VolSurge, NewsIntensity, EventSeverity, InformationGap.
- Returns a **0‑100** composite risk score.
- Categorizes alerts into BRD priority tiers: CRITICAL (>=85), HIGH (70-84), MEDIUM (50-69), LOW (<50).
- Validates the weight vector (non‑negative, sums to ≈ 1.0).
- Explicit InformationGap factor without hidden ad-hoc penalties.
- Configurable no‑news confidence (default 0.50).
"""

from dataclasses import dataclass
from typing import Dict, Optional

from intelligence.correlation.temporal_aligner import (
    CorrelationEvidencePair,
    TemporalRelationshipType,
)


@dataclass(frozen=True)
class RiskScoreBreakdown:
    """Breakdown of the five BRD‑specified risk components.

    All values are expressed on the **0‑100** scale to match the final score.
    """
    anomaly_score: float
    vol_surge: float
    news_intensity: float
    event_severity: float
    information_gap: float


@dataclass(frozen=True)
class CompositeRiskScoreResult:
    """Result object returned by ``calculate_risk``.

    ``composite_risk_score`` – final score on the **0‑100** scale.
    ``confidence`` – confidence in the evaluation (0‑1).
    ``priority_tier`` – CRITICAL (>=85), HIGH (70-84), MEDIUM (50-69), LOW (<50).
    """
    composite_risk_score: float  # 0‑100
    confidence: float  # 0‑1
    breakdown: RiskScoreBreakdown
    primary_risk_driver: str
    is_actionable_alert: bool
    priority_tier: str = "MEDIUM"


class MultiDimensionalRiskScorer:
    """BRD‑compliant risk scorer implementing FR-5.2 and FR-5.3."""

    # Default weights – sum to 1.0
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "anomaly_score": 0.30,
        "vol_surge": 0.20,
        "news_intensity": 0.20,
        "event_severity": 0.15,
        "information_gap": 0.15,
    }

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        actionable_threshold: float = 50.0,
        no_news_confidence: float = 0.50,
        dynamic_no_news_confidence: bool = False,
    ):
        raw_weights = weights or self.DEFAULT_WEIGHTS
        self._validate_weights(raw_weights)
        # Normalize weights to guarantee exact sum = 1.0 (Issue 34)
        total = sum(raw_weights.values())
        self.weights = {k: v / total for k, v in raw_weights.items()}
        self.actionable_threshold = actionable_threshold
        self.no_news_confidence = no_news_confidence
        self.dynamic_no_news_confidence = dynamic_no_news_confidence

    @staticmethod
    def _validate_weights(weights: Dict[str, float]) -> None:
        total = sum(weights.values())
        if any(w < 0 for w in weights.values()):
            raise ValueError("Risk scorer weights must be non‑negative.")
        if not (0.99 <= total <= 1.01):
            raise ValueError(
                f"Risk scorer weights must sum to 1.0 (got {total:.3f})."
            )
        required_keys = {
            "anomaly_score",
            "vol_surge",
            "news_intensity",
            "event_severity",
            "information_gap",
        }
        missing = required_keys - set(weights.keys())
        if missing:
            raise ValueError(f"Missing required weight keys: {missing}")

    @staticmethod
    def _scale_to_100(value: float) -> float:
        """Clamp ``value`` to [0,1] and return the 0‑100 representation."""
        return round(min(1.0, max(0.0, value)) * 100, 3)

    @staticmethod
    def compute_priority_tier(score: float) -> str:
        """Assign investigation priority tier per FR-5.3."""
        if score >= 85.0:
            return "CRITICAL"
        if score >= 70.0:
            return "HIGH"
        if score >= 50.0:
            return "MEDIUM"
        return "LOW"

    def calculate_risk(self, pair: CorrelationEvidencePair) -> CompositeRiskScoreResult:
        """Calculate the composite risk score for a market‑news evidence pair.

        Returns ``CompositeRiskScoreResult`` with a 0‑100 ``composite_risk_score``.
        """
        m_snap = pair.market_snapshot
        n_snap = pair.news_snapshot

        # Factor 1: AnomalyScore (direct market anomaly)
        anomaly_score_raw = min(1.0, max(0.0, m_snap.ensemble_score))
        anomaly_score = self._scale_to_100(anomaly_score_raw)

        # Factor 2: VolSurge (price & volume volatility)
        ret_component = abs(m_snap.return_zscore) / 5.0
        vol_component = abs(m_snap.volume_zscore) / 5.0
        vol_surge_raw = min(1.0, (ret_component + vol_component) / 2.0)
        vol_surge = self._scale_to_100(vol_surge_raw)

        # Factor 3: NewsIntensity (how strongly the news relates)
        if n_snap is not None:
            news_intensity_raw = min(1.0, max(0.0, n_snap.surveillance_relevance))
        else:
            news_intensity_raw = 0.0
        news_intensity = self._scale_to_100(news_intensity_raw)

        # Factor 4: EventSeverity (sentiment magnitude)
        if n_snap is not None:
            event_severity_raw = min(1.0, abs(n_snap.sentiment_compound))
        else:
            event_severity_raw = 0.0
        event_severity = self._scale_to_100(event_severity_raw)

        # Factor 5: InformationGap (temporal relationship)
        if pair.relationship_type == TemporalRelationshipType.UNEXPLAINED_ABSENCE:
            information_gap_raw = 1.0
        else:
            information_gap_raw = max(0.0, 1.0 - pair.temporal_proximity_weight)
        information_gap = self._scale_to_100(information_gap_raw)

        # Weighted composite calculation on 0‑100 scale
        raw_score = (
            self.weights["anomaly_score"] * anomaly_score
            + self.weights["vol_surge"] * vol_surge
            + self.weights["news_intensity"] * news_intensity
            + self.weights["event_severity"] * event_severity
            + self.weights["information_gap"] * information_gap
        )
        composite_score = round(min(100.0, max(0.0, raw_score)), 3)

        # Primary risk driver
        contributions = {
            "Market Anomaly": self.weights["anomaly_score"] * anomaly_score,
            "Volatility Surge": self.weights["vol_surge"] * vol_surge,
            "News Intensity": self.weights["news_intensity"] * news_intensity,
            "Event Severity": self.weights["event_severity"] * event_severity,
            "Information Gap": self.weights["information_gap"] * information_gap,
        }
        primary_driver = max(contributions.items(), key=lambda x: x[1])[0]

        # Confidence (Issue 32: dynamic based on temporal evidence or anomaly signal-to-noise ratio)
        if n_snap is not None:
            confidence = min(1.0, 0.75 + (pair.temporal_proximity_weight * 0.25))
        elif self.dynamic_no_news_confidence:
            confidence = min(0.85, max(0.20, round(self.no_news_confidence + (m_snap.ensemble_score - 0.5) * 0.25, 3)))
        else:
            confidence = self.no_news_confidence

        breakdown = RiskScoreBreakdown(
            anomaly_score=anomaly_score,
            vol_surge=vol_surge,
            news_intensity=news_intensity,
            event_severity=event_severity,
            information_gap=information_gap,
        )

        priority_tier = self.compute_priority_tier(composite_score)

        return CompositeRiskScoreResult(
            composite_risk_score=composite_score,
            confidence=round(confidence, 3),
            breakdown=breakdown,
            primary_risk_driver=primary_driver,
            is_actionable_alert=composite_score >= self.actionable_threshold,
            priority_tier=priority_tier,
        )
