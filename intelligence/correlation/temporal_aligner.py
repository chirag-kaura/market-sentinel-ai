"""
Market-News Temporal Correlation and Window Alignment Module.
Phase 8 — Step 8.1: Pairs market time-series anomaly events with news disclosures
across calibrated lead/lag windows (-48h to +24h) to classify information leakage.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import math
from typing import List, Optional, Tuple


class TemporalRelationshipType(str, Enum):
    PRE_ANNOUNCEMENT_LEAK = "PRE_ANNOUNCEMENT_LEAK"       # Market anomaly occurred BEFORE news (suspected insider leak/front-running)
    COINCIDENT_REACTION = "COINCIDENT_REACTION"           # Market anomaly coincided with news release (standard absorption)
    POST_NEWS_ABSORPTION = "POST_NEWS_ABSORPTION"         # Market anomaly followed after news release (lagged public reaction)
    UNEXPLAINED_ABSENCE = "UNEXPLAINED_ABSENCE"           # Market anomaly with NO coinciding news (suspected manipulation/spoofing)


@dataclass(frozen=True)
class TemporalWindowConfig:
    """Configuration for correlation lead/lag search windows."""
    pre_event_window_hours: float = 48.0   # Look back up to 48 hours for earlier news or market moves
    post_event_window_hours: float = 24.0  # Look forward up to 24 hours
    coincident_threshold_hours: float = 2.0  # Within +/- 2 hours is considered coincident
    decay_halflife_hours: float = 12.0     # Time decay half-life for proximity weighting


@dataclass(frozen=True)
class MarketAnomalySnapshot:
    """Snapshot of a detected market anomaly point from Phase 6."""
    timestamp: datetime
    ticker: str
    ensemble_score: float
    severity_tier: str
    return_zscore: float
    volume_zscore: float


@dataclass(frozen=True)
class NewsEventSnapshot:
    """Snapshot of an ingested and processed news event from Phase 7."""
    story_id: str
    headline: str
    timestamp: datetime
    primary_event: str
    sentiment_compound: float
    surveillance_relevance: float
    source: str


@dataclass(frozen=True)
class CorrelationEvidencePair:
    """Unified temporal evidence binding market anomaly to news context."""
    market_snapshot: MarketAnomalySnapshot
    news_snapshot: Optional[NewsEventSnapshot]
    relationship_type: TemporalRelationshipType
    time_delta_hours: Optional[float]  # positive: news came AFTER market move (lead); negative: news came BEFORE
    temporal_proximity_weight: float    # Exponential decay weight [0.0, 1.0]
    suspicion_multiplier: float         # Elevated when market moved prior to critical disclosure


class TemporalCorrelationAligner:
    """
    Pairs market anomaly observations with contemporaneous or forward news events
    for a given equity ticker without look-ahead bias.
    """

    def __init__(self, config: Optional[TemporalWindowConfig] = None):
        self.config = config or TemporalWindowConfig()
        self._decay_lambda = math.log(2) / (self.config.decay_halflife_hours * 3600)

    def align(
        self,
        market_anomaly: MarketAnomalySnapshot,
        candidate_news: List[NewsEventSnapshot]
    ) -> CorrelationEvidencePair:
        """
        Aligns a market anomaly snapshot with the closest / most relevant candidate news story.
        """
        m_time = market_anomaly.timestamp
        if m_time.tzinfo is None:
            m_time = m_time.replace(tzinfo=timezone.utc)

        if not candidate_news:
            return CorrelationEvidencePair(
                market_snapshot=market_anomaly,
                news_snapshot=None,
                relationship_type=TemporalRelationshipType.UNEXPLAINED_ABSENCE,
                time_delta_hours=None,
                temporal_proximity_weight=0.0,
                suspicion_multiplier=1.25  # Unexplained anomalies carry high investigative suspicion
            )

        # Filter candidate news within the permissible temporal window:
        # news can be up to pre_event_window_hours BEFORE market, or post_event_window_hours AFTER market
        valid_candidates: List[Tuple[NewsEventSnapshot, float]] = []

        for news in candidate_news:
            n_time = news.timestamp
            if n_time.tzinfo is None:
                n_time = n_time.replace(tzinfo=timezone.utc)

            delta_seconds = (n_time - m_time).total_seconds()
            delta_hours = delta_seconds / 3600.0

            # Delta check: -pre_event_window <= delta_hours <= post_event_window
            if -self.config.pre_event_window_hours <= delta_hours <= self.config.post_event_window_hours:
                valid_candidates.append((news, delta_hours))

        if not valid_candidates:
            return CorrelationEvidencePair(
                market_snapshot=market_anomaly,
                news_snapshot=None,
                relationship_type=TemporalRelationshipType.UNEXPLAINED_ABSENCE,
                time_delta_hours=None,
                temporal_proximity_weight=0.0,
                suspicion_multiplier=1.25
            )

        # Select candidate news by minimizing temporal distance, prioritizing high surveillance relevance
        # Score = relevance / (1.0 + abs(delta_hours) * 0.1)
        best_candidate, best_delta_hours = max(
            valid_candidates,
            key=lambda pair: (pair[0].surveillance_relevance / (1.0 + abs(pair[1]) * 0.05))
        )

        abs_delta_seconds = abs(best_delta_hours * 3600.0)
        proximity_weight = math.exp(-self._decay_lambda * abs_delta_seconds)

        # Classify relationship based on delta_hours
        # best_delta_hours = t_news - t_market
        # If delta > +threshold => news came AFTER market moved => PRE_ANNOUNCEMENT_LEAK
        if best_delta_hours > self.config.coincident_threshold_hours:
            rel_type = TemporalRelationshipType.PRE_ANNOUNCEMENT_LEAK
            suspicion_mult = 1.40  # Highest suspicion: front-running before disclosure
        elif best_delta_hours < -self.config.coincident_threshold_hours:
            rel_type = TemporalRelationshipType.POST_NEWS_ABSORPTION
            suspicion_mult = 0.85  # Normal absorption of already-public news
        else:
            rel_type = TemporalRelationshipType.COINCIDENT_REACTION
            suspicion_mult = 1.00  # Expected market reaction to live announcement

        return CorrelationEvidencePair(
            market_snapshot=market_anomaly,
            news_snapshot=best_candidate,
            relationship_type=rel_type,
            time_delta_hours=round(best_delta_hours, 2),
            temporal_proximity_weight=round(proximity_weight, 3),
            suspicion_multiplier=suspicion_mult
        )
