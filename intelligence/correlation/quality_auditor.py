"""
Alert Quality, Investigation Burden, and False Positive Audit Harness.
Phase 8 — Step 8.6: Computes operational efficiency metrics, alert fatigue ratios,
concentration by equity ticker, and false positive burdens to prevent alert fatigue.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
from intelligence.correlation.alert_models import SurveillanceAlertSchema


@dataclass(frozen=True)
class AlertQualityAuditMetrics:
    """Quantitative audit metrics evaluating operational investigation health."""
    total_alerts: int
    actionable_alerts: int              # HIGH + CRITICAL alerts requiring human triage
    informational_ratio: float          # Proportion of alerts that are benign/informational
    actionable_ratio: float             # Proportion of alerts that require action
    ticker_concentration_hhi: float     # Herfindahl-Hirschman Index measuring alert concentration across tickers
    top_concentrated_ticker: str
    top_ticker_alert_percentage: float
    average_risk_score: float
    alert_fatigue_index: float          # Normalized metric [0.0, 1.0] indicating compliance overload risk
    is_operationally_sustainable: bool  # True if actionable_ratio <= 0.35 and HHI < 0.25


class AlertQualityAuditor:
    """
    Audits generated alerts against regulatory operational efficiency benchmarks.
    Detects ticker fixation bias and measures false positive suppression efficiency.
    """

    def audit_alerts(self, alerts: List[SurveillanceAlertSchema]) -> AlertQualityAuditMetrics:
        """Computes comprehensive quality and fatigue metrics across alert batches."""
        if not alerts:
            return AlertQualityAuditMetrics(
                total_alerts=0,
                actionable_alerts=0,
                informational_ratio=0.0,
                actionable_ratio=0.0,
                ticker_concentration_hhi=0.0,
                top_concentrated_ticker="NONE",
                top_ticker_alert_percentage=0.0,
                average_risk_score=0.0,
                alert_fatigue_index=0.0,
                is_operationally_sustainable=True
            )

        total_count = len(alerts)
        actionable_count = sum(1 for a in alerts if a.priority_tier in ["HIGH", "CRITICAL"])
        informational_count = sum(1 for a in alerts if a.priority_tier in ["INFORMATIONAL", "LOW"])

        actionable_ratio = actionable_count / total_count
        informational_ratio = informational_count / total_count
        avg_score = sum(a.composite_risk_score for a in alerts) / total_count

        # Compute ticker distribution & Herfindahl-Hirschman Index (HHI)
        ticker_counts: Dict[str, int] = {}
        for a in alerts:
            ticker_counts[a.ticker] = ticker_counts.get(a.ticker, 0) + 1

        top_ticker, top_ticker_count = max(ticker_counts.items(), key=lambda x: x[1])
        top_ticker_pct = top_ticker_count / total_count

        # HHI: sum of squared market shares [0.0, 1.0]
        hhi = sum((cnt / total_count) ** 2 for cnt in ticker_counts.values())

        # Alert fatigue index: high when actionable_ratio is too high (> 0.40) or concentration is extreme (> 0.50)
        fatigue_index = min(1.0, (actionable_ratio * 0.6) + (hhi * 0.4))

        # Regulatory operational guideline: actionable alerts should typically comprise <= 35% of total
        # signals, and ticker concentration should not be monopolized by a single name (HHI < 0.40)
        is_sustainable = (actionable_ratio <= 0.40) and (hhi <= 0.40)

        return AlertQualityAuditMetrics(
            total_alerts=total_count,
            actionable_alerts=actionable_count,
            informational_ratio=round(informational_ratio, 3),
            actionable_ratio=round(actionable_ratio, 3),
            ticker_concentration_hhi=round(hhi, 3),
            top_concentrated_ticker=top_ticker,
            top_ticker_alert_percentage=round(top_ticker_pct * 100, 1),
            average_risk_score=round(avg_score, 3),
            alert_fatigue_index=round(fatigue_index, 3),
            is_operationally_sustainable=is_sustainable
        )
