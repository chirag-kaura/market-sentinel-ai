"""
Historical Replay and Market Backtesting Harness.
Phase 8 — Step 8.5: Simulates the chronological execution of the surveillance pipeline
over historical market-news sequences without look-ahead bias.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from intelligence.correlation.temporal_aligner import (
    TemporalCorrelationAligner,
    TemporalWindowConfig,
    MarketAnomalySnapshot,
    NewsEventSnapshot,
)
from intelligence.correlation.risk_scorer import MultiDimensionalRiskScorer
from intelligence.correlation.alert_prioritizer import AlertPrioritizer
from intelligence.correlation.alert_models import SurveillanceAlertSchema


@dataclass(frozen=True)
class HistoricalReplaySummary:
    """Statistical summary of backtested historical surveillance execution."""
    total_market_bars_evaluated: int
    total_news_items_evaluated: int
    total_alerts_generated: int
    critical_alerts_count: int
    high_alerts_count: int
    medium_alerts_count: int
    low_alerts_count: int
    informational_alerts_count: int
    actionable_alert_ratio: float


class HistoricalSurveillanceReplayHarness:
    """
    Chronological replay simulator executing market anomaly detection, news correlation,
    and alert generation strictly using point-in-time available data.
    """

    def __init__(
        self,
        aligner: Optional[TemporalCorrelationAligner] = None,
        risk_scorer: Optional[MultiDimensionalRiskScorer] = None,
        prioritizer: Optional[AlertPrioritizer] = None,
    ):
        self.aligner = aligner or TemporalCorrelationAligner()
        self.risk_scorer = risk_scorer or MultiDimensionalRiskScorer()
        self.prioritizer = prioritizer or AlertPrioritizer()

    def run_replay(
        self,
        market_anomalies: List[MarketAnomalySnapshot],
        historical_news: List[NewsEventSnapshot]
    ) -> Tuple[List[SurveillanceAlertSchema], HistoricalReplaySummary]:
        """
        Executes point-in-time historical simulation over chronological anomaly events.
        """
        # Ensure chronological ordering
        sorted_anomalies = sorted(market_anomalies, key=lambda a: a.timestamp)
        sorted_news = sorted(historical_news, key=lambda n: n.timestamp)

        generated_alerts: List[SurveillanceAlertSchema] = []
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFORMATIONAL": 0}

        alert_idx = 1
        for anomaly in sorted_anomalies:
            a_time = anomaly.timestamp
            if a_time.tzinfo is None:
                a_time = a_time.replace(tzinfo=timezone.utc)

            # Causal Window Filtering: Only include news published up to post_event_window_hours
            # after the anomaly, and no later than the backtest simulation horizon
            max_horizon = a_time.timestamp() + (self.aligner.config.post_event_window_hours * 3600)
            available_news = [
                n for n in sorted_news
                if (n.timestamp.timestamp() if n.timestamp.tzinfo else n.timestamp.replace(tzinfo=timezone.utc).timestamp()) <= max_horizon
            ]

            # 1. Temporal Correlation
            evidence_pair = self.aligner.align(anomaly, available_news)

            # 2. Risk Scoring
            risk_result = self.risk_scorer.calculate_risk(evidence_pair)

            # 3. Prioritization
            prioritization = self.prioritizer.prioritize(risk_result)
            tier_str = prioritization.priority_tier.value
            counts[tier_str] = counts.get(tier_str, 0) + 1

            # 4. Packaging into Standardized Schema
            alert_id = f"ALT_REPLAY_{anomaly.ticker}_{alert_idx:04d}"
            alert_idx += 1

            market_snap_dict = {
                "ensemble_score": anomaly.ensemble_score,
                "severity_tier": anomaly.severity_tier,
                "return_zscore": anomaly.return_zscore,
                "volume_zscore": anomaly.volume_zscore
            }

            news_snap_dict = None
            if evidence_pair.news_snapshot is not None:
                news_snap_dict = {
                    "story_id": evidence_pair.news_snapshot.story_id,
                    "headline": evidence_pair.news_snapshot.headline,
                    "event": evidence_pair.news_snapshot.primary_event,
                    "sentiment": evidence_pair.news_snapshot.sentiment_compound,
                    "relevance": evidence_pair.news_snapshot.surveillance_relevance,
                    "source": evidence_pair.news_snapshot.source
                }

            breakdown_dict = {
                "anomaly_score": risk_result.breakdown.anomaly_score,
                "vol_surge": risk_result.breakdown.vol_surge,
                "news_intensity": risk_result.breakdown.news_intensity,
                "event_severity": risk_result.breakdown.event_severity,
                "information_gap": risk_result.breakdown.information_gap
            }

            alert = SurveillanceAlertSchema(
                alert_id=alert_id,
                ticker=f"NSE:{anomaly.ticker}",
                company_name=anomaly.ticker,
                alert_timestamp=anomaly.timestamp,
                priority_tier=tier_str,
                composite_risk_score=risk_result.composite_risk_score,
                confidence=risk_result.confidence,
                primary_risk_driver=prioritization.primary_risk_driver,
                temporal_relationship=evidence_pair.relationship_type.value,
                sla_triage_hours=prioritization.sla_triage_hours,
                requires_human_escalation=prioritization.requires_human_escalation,
                recommended_action=prioritization.recommended_action,
                market_snapshot=market_snap_dict,
                news_snapshot=news_snap_dict,
                risk_breakdown=breakdown_dict,
                status="OPEN"
            )
            generated_alerts.append(alert)

        total_alerts = len(generated_alerts)
        actionable_count = counts["CRITICAL"] + counts["HIGH"]
        actionable_ratio = (actionable_count / total_alerts) if total_alerts > 0 else 0.0

        summary = HistoricalReplaySummary(
            total_market_bars_evaluated=len(market_anomalies),
            total_news_items_evaluated=len(historical_news),
            total_alerts_generated=total_alerts,
            critical_alerts_count=counts["CRITICAL"],
            high_alerts_count=counts["HIGH"],
            medium_alerts_count=counts["MEDIUM"],
            low_alerts_count=counts["LOW"],
            informational_alerts_count=counts["INFORMATIONAL"],
            actionable_alert_ratio=round(actionable_ratio, 3)
        )

        return generated_alerts, summary
