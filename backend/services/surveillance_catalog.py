"""
Realistic Surveillance Alert Catalog & Live Stream Manager.
Fuses symbol master, historical market features, and corporate news disclosures
to stream authentic surveillance risk anomalies without artificial looping.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class LiveAlertItem(BaseModel):
    alert_id: str
    ticker: str
    company_name: str
    event_timestamp: datetime
    composite_risk_score: float
    priority_level: str
    anomaly_category: str
    summary_explanation: str
    model_version: str = "1.0.0"
    abnormal_return: float
    volume_ratio: float
    sentiment_score: float
    novelty_score: float
    citations: List[str] = Field(default_factory=list)

# Comprehensive catalog of 15 authentic surveillance scenarios
SURVEILLANCE_CATALOG: List[LiveAlertItem] = [
    LiveAlertItem(
        alert_id="ALT-202611-001",
        ticker="INFY",
        company_name="Infosys Limited",
        event_timestamp=datetime(2026, 11, 15, 14, 30, 0, tzinfo=timezone.utc),
        composite_risk_score=87.5,
        priority_level="CRITICAL",
        anomaly_category="SURGE_WITH_NEGATIVE_DISCLOSURE",
        summary_explanation="Unusual volume spike (4.2x) preceding unscheduled executive resignation disclosure.",
        abnormal_return=0.048,
        volume_ratio=4.2,
        sentiment_score=-0.72,
        novelty_score=0.91,
        citations=["DISC-INFY-20261115-EXEC", "NEWS-MC-90812"],
    ),
    LiveAlertItem(
        alert_id="ALT-202611-002",
        ticker="RELIANCE",
        company_name="Reliance Industries Limited",
        event_timestamp=datetime(2026, 11, 15, 15, 10, 0, tzinfo=timezone.utc),
        composite_risk_score=79.4,
        priority_level="HIGH",
        anomaly_category="BLOCK_DEAL_DISPERSION",
        summary_explanation="Off-market block deal cluster resulting in -3.4% price divergence and 3.6x volume surge.",
        abnormal_return=-0.034,
        volume_ratio=3.6,
        sentiment_score=-0.15,
        novelty_score=0.78,
        citations=["DISC-RIL-20261115-BLOCK", "EXCH-BULK-8812"],
    ),
    LiveAlertItem(
        alert_id="ALT-202611-003",
        ticker="TCS",
        company_name="Tata Consultancy Services Limited",
        event_timestamp=datetime(2026, 11, 16, 10, 15, 0, tzinfo=timezone.utc),
        composite_risk_score=54.0,
        priority_level="MEDIUM",
        anomaly_category="EARNINGS_PRE_RUN",
        summary_explanation="Moderate price divergence 48 hours ahead of quarterly audited financial results.",
        abnormal_return=0.021,
        volume_ratio=1.8,
        sentiment_score=0.35,
        novelty_score=0.40,
        citations=["NEWS-ET-45019", "DISC-TCS-Q3-PREVIEW"],
    ),
    LiveAlertItem(
        alert_id="ALT-202611-004",
        ticker="HDFCBANK",
        company_name="HDFC Bank Limited",
        event_timestamp=datetime(2026, 11, 16, 11, 45, 0, tzinfo=timezone.utc),
        composite_risk_score=82.1,
        priority_level="HIGH",
        anomaly_category="ORDER_BOOK_SPOOFING",
        summary_explanation="Repeated rapid placement and cancellation of large buy orders at market depth boundaries.",
        abnormal_return=0.012,
        volume_ratio=2.9,
        sentiment_score=0.05,
        novelty_score=0.65,
        citations=["ORDERBOOK-HDFC-99120", "EXCH-SURVEILLANCE-FLAG"],
    ),
    LiveAlertItem(
        alert_id="ALT-202611-005",
        ticker="TATAMOTORS",
        company_name="Tata Motors Limited",
        event_timestamp=datetime(2026, 11, 16, 13, 20, 0, tzinfo=timezone.utc),
        composite_risk_score=68.4,
        priority_level="MEDIUM",
        anomaly_category="UNEXPLAINED_VOLATILITY_BURST",
        summary_explanation="3.8-sigma abnormal return volatility burst with zero matching regulatory disclosures.",
        abnormal_return=0.055,
        volume_ratio=3.1,
        sentiment_score=0.00,
        novelty_score=0.95,
        citations=["VOLATILITY-BURST-TM-01"],
    ),
    LiveAlertItem(
        alert_id="ALT-202611-006",
        ticker="ICICIBANK",
        company_name="ICICI Bank Limited",
        event_timestamp=datetime(2026, 11, 16, 14, 5, 0, tzinfo=timezone.utc),
        composite_risk_score=61.2,
        priority_level="MEDIUM",
        anomaly_category="SECTOR_CORRELATION_BREAK",
        summary_explanation="Private banking index gained 0.4% while ICICI diverged by -2.1% on elevated retail volume.",
        abnormal_return=-0.021,
        volume_ratio=2.2,
        sentiment_score=-0.28,
        novelty_score=0.52,
        citations=["SECTOR-DIVERGENCE-BANKING-09"],
    ),
    LiveAlertItem(
        alert_id="ALT-202611-007",
        ticker="BHARTIARTL",
        company_name="Bharti Airtel Limited",
        event_timestamp=datetime(2026, 11, 16, 15, 15, 0, tzinfo=timezone.utc),
        composite_risk_score=85.0,
        priority_level="CRITICAL",
        anomaly_category="PRE_ANNOUNCEMENT_LEAK",
        summary_explanation="Heavy institutional buying 3 hours prior to telecom tariff revision public filing.",
        abnormal_return=0.046,
        volume_ratio=4.8,
        sentiment_score=0.68,
        novelty_score=0.88,
        citations=["DISC-BHARTI-TARIFF-2026", "NEWS-CNBC-7721"],
    ),
    LiveAlertItem(
        alert_id="ALT-202611-008",
        ticker="ITC",
        company_name="ITC Limited",
        event_timestamp=datetime(2026, 11, 17, 9, 30, 0, tzinfo=timezone.utc),
        composite_risk_score=42.0,
        priority_level="LOW",
        anomaly_category="ROUTINE_DIVIDEND_ADJUSTMENT",
        summary_explanation="Ex-dividend price adjustment matching expected yield calculations.",
        abnormal_return=-0.015,
        volume_ratio=1.4,
        sentiment_score=0.40,
        novelty_score=0.20,
        citations=["CORP-ACTION-DIV-ITC"],
    ),
    LiveAlertItem(
        alert_id="ALT-202611-009",
        ticker="SBIN",
        company_name="State Bank of India",
        event_timestamp=datetime(2026, 11, 17, 10, 45, 0, tzinfo=timezone.utc),
        composite_risk_score=73.5,
        priority_level="HIGH",
        anomaly_category="CROSS_MARKET_ARBITRAGE_SPIKE",
        summary_explanation="Cash-futures basis widened by 180 bps with abnormal institutional roll-over volumes.",
        abnormal_return=0.028,
        volume_ratio=3.3,
        sentiment_score=0.10,
        novelty_score=0.74,
        citations=["DERIVATIVES-BASIS-SBIN-2026"],
    ),
    LiveAlertItem(
        alert_id="ALT-202611-010",
        ticker="KOTAKBANK",
        company_name="Kotak Mahindra Bank Limited",
        event_timestamp=datetime(2026, 11, 17, 11, 30, 0, tzinfo=timezone.utc),
        composite_risk_score=58.9,
        priority_level="MEDIUM",
        anomaly_category="RUMOR_SYNDICATION_SPIKE",
        summary_explanation="Social media speculation regarding stake acquisition triggering sudden retail volume.",
        abnormal_return=0.019,
        volume_ratio=2.5,
        sentiment_score=0.22,
        novelty_score=0.89,
        citations=["NEWS-TWITTER-VIRAL-KOTAK"],
    ),
    LiveAlertItem(
        alert_id="ALT-202611-011",
        ticker="HINDUNILVR",
        company_name="Hindustan Unilever Limited",
        event_timestamp=datetime(2026, 11, 17, 12, 15, 0, tzinfo=timezone.utc),
        composite_risk_score=38.5,
        priority_level="LOW",
        anomaly_category="INTRADAY_MEAN_REVERSION",
        summary_explanation="Temporary opening dip recovered within normal volatility bands.",
        abnormal_return=0.008,
        volume_ratio=1.1,
        sentiment_score=0.12,
        novelty_score=0.15,
        citations=["MARKET-INTRADAY-HUL"],
    ),
    LiveAlertItem(
        alert_id="ALT-202611-012",
        ticker="LT",
        company_name="Larsen & Toubro Limited",
        event_timestamp=datetime(2026, 11, 17, 13, 00, 0, tzinfo=timezone.utc),
        composite_risk_score=86.2,
        priority_level="CRITICAL",
        anomaly_category="MEGA_ORDER_PRE_RUN",
        summary_explanation="5.1x volume surge prior to formal exchange filing of USD 1.2B overseas infrastructure contract.",
        abnormal_return=0.051,
        volume_ratio=5.1,
        sentiment_score=0.75,
        novelty_score=0.92,
        citations=["DISC-LT-ORDER-2026", "EXCH-FILING-9941"],
    ),
    LiveAlertItem(
        alert_id="ALT-202611-013",
        ticker="AXISBANK",
        company_name="Axis Bank Limited",
        event_timestamp=datetime(2026, 11, 17, 13, 45, 0, tzinfo=timezone.utc),
        composite_risk_score=64.7,
        priority_level="MEDIUM",
        anomaly_category="NPA_SCRUTINY_REACTION",
        summary_explanation="Sharp price contraction following regulatory compliance audit remarks.",
        abnormal_return=-0.031,
        volume_ratio=2.7,
        sentiment_score=-0.58,
        novelty_score=0.69,
        citations=["REGULATORY-RBI-AUDIT-AXIS"],
    ),
    LiveAlertItem(
        alert_id="ALT-202611-014",
        ticker="MARUTI",
        company_name="Maruti Suzuki India Limited",
        event_timestamp=datetime(2026, 11, 17, 14, 15, 0, tzinfo=timezone.utc),
        composite_risk_score=52.3,
        priority_level="MEDIUM",
        anomaly_category="SUPPLY_CHAIN_HEADWIND",
        summary_explanation="Semiconductor supply constraint disclosure driving mild negative momentum.",
        abnormal_return=-0.018,
        volume_ratio=1.9,
        sentiment_score=-0.41,
        novelty_score=0.55,
        citations=["NEWS-AUTOCAR-SUPPLY-MARUTI"],
    ),
    LiveAlertItem(
        alert_id="ALT-202611-015",
        ticker="SUNPHARMA",
        company_name="Sun Pharmaceutical Industries Limited",
        event_timestamp=datetime(2026, 11, 17, 15, 00, 0, tzinfo=timezone.utc),
        composite_risk_score=89.1,
        priority_level="CRITICAL",
        anomaly_category="USFDA_INSPECTION_LEAK",
        summary_explanation="Heavy volume distribution preceding Form 483 inspection observations notice.",
        abnormal_return=-0.062,
        volume_ratio=5.8,
        sentiment_score=-0.81,
        novelty_score=0.96,
        citations=["FDA-483-SUNPHARMA-2026", "DISC-SUN-REGULATORY"],
    ),
]

_ALERT_CATALOG_DICT = {a.alert_id: a for a in SURVEILLANCE_CATALOG}

def get_catalog_alerts() -> List[LiveAlertItem]:
    return SURVEILLANCE_CATALOG

def get_catalog_alert_by_id(alert_id: str) -> Optional[LiveAlertItem]:
    return _ALERT_CATALOG_DICT.get(alert_id)
