"""Market-News Correlation Intelligence Package Initialization."""
from intelligence.correlation.temporal_aligner import (
    TemporalCorrelationAligner,
    TemporalWindowConfig,
    TemporalRelationshipType,
    MarketAnomalySnapshot,
    NewsEventSnapshot,
    CorrelationEvidencePair,
)
from intelligence.correlation.risk_scorer import (
    MultiDimensionalRiskScorer,
    CompositeRiskScoreResult,
    RiskScoreBreakdown,
)
from intelligence.correlation.alert_prioritizer import (
    AlertPrioritizer,
    AlertPriorityTier,
    AlertPrioritizationResult,
)
from intelligence.correlation.alert_models import (
    SurveillanceAlertSchema,
    SurveillanceAlertModel,
)
from intelligence.correlation.backtesting_harness import (
    HistoricalSurveillanceReplayHarness,
    HistoricalReplaySummary,
)
from intelligence.correlation.quality_auditor import (
    AlertQualityAuditor,
    AlertQualityAuditMetrics,
)

__all__ = [
    "TemporalCorrelationAligner",
    "TemporalWindowConfig",
    "TemporalRelationshipType",
    "MarketAnomalySnapshot",
    "NewsEventSnapshot",
    "CorrelationEvidencePair",
    "MultiDimensionalRiskScorer",
    "CompositeRiskScoreResult",
    "RiskScoreBreakdown",
    "AlertPrioritizer",
    "AlertPriorityTier",
    "AlertPrioritizationResult",
    "SurveillanceAlertSchema",
    "SurveillanceAlertModel",
    "HistoricalSurveillanceReplayHarness",
    "HistoricalReplaySummary",
    "AlertQualityAuditor",
    "AlertQualityAuditMetrics",
]
