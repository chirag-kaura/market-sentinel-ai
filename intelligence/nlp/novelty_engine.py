"""
News Novelty and Intensity Quantification Engine.
Phase 7 — Step 7.6: Tracks story repetition, detects breaking news bursts,
evaluates source diversity, and quantifies decay-weighted news intensity.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class StoryClusterRecord:
    """Historical representation of an ingested story for novelty tracking."""
    story_id: str
    ticker: str
    headline: str
    timestamp: datetime
    source: str
    content_hash: str
    token_set: Set[str]


@dataclass(frozen=True)
class NoveltyIntensityResult:
    """Structured novelty and burst intensity metrics for a news event."""
    story_id: str
    ticker: str
    is_novel: bool
    novelty_score: float  # Scale 0.0 (exact duplicate/stale) to 1.0 (completely new story)
    cluster_size_24h: int
    source_diversity_count: int
    decay_weighted_intensity: float
    is_breaking_burst: bool  # True if news count in 4h exceeds burst threshold


class NewsNoveltyIntensityEngine:
    """
    Evaluates incoming financial news against rolling historical clusters per ticker.
    Identifies duplicate syndications, decay-weighted news velocity, and burst events.
    """

    def __init__(
        self,
        jaccard_duplicate_threshold: float = 0.70,
        decay_halflife_hours: float = 6.0,
        burst_threshold_count: int = 3
    ):
        self.jaccard_threshold = jaccard_duplicate_threshold
        self.decay_halflife_hours = decay_halflife_hours
        self.burst_threshold_count = burst_threshold_count
        # In-memory historical buffer indexed by ticker: ticker -> List[StoryClusterRecord]
        self._history: Dict[str, List[StoryClusterRecord]] = {}

    def process_story(
        self,
        story_id: str,
        ticker: str,
        headline: str,
        timestamp: datetime,
        source: str,
        content_hash: str
    ) -> NoveltyIntensityResult:
        """Processes an incoming story and quantifies its novelty and intensity."""
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        tokens = set(headline.lower().split())

        history = self._history.setdefault(ticker, [])

        # Filter history to the trailing 24 hours relative to current story timestamp
        recent_cutoff_seconds = 24 * 3600
        recent_stories = [
            s for s in history
            if 0 <= (timestamp - s.timestamp).total_seconds() <= recent_cutoff_seconds
        ]

        if not recent_stories:
            # First story for this ticker in 24 hours: Maximum novelty
            novelty_score = 1.0
            is_novel = True
            cluster_size = 1
            source_diversity = 1
            decay_intensity = 1.0
            is_burst = False
        else:
            # Check for exact hash duplicates or high Jaccard headline overlap
            max_similarity = 0.0
            for prev_story in recent_stories:
                if prev_story.content_hash == content_hash:
                    max_similarity = 1.0
                    break
                # Jaccard overlap on headline tokens
                if tokens and prev_story.token_set:
                    inter = len(tokens.intersection(prev_story.token_set))
                    union = len(tokens.union(prev_story.token_set))
                    sim = inter / union if union > 0 else 0.0
                    if sim > max_similarity:
                        max_similarity = sim

            novelty_score = max(0.0, 1.0 - max_similarity)
            is_novel = max_similarity < self.jaccard_threshold

            cluster_size = len(recent_stories) + 1
            distinct_sources = {s.source for s in recent_stories}.union({source})
            source_diversity = len(distinct_sources)

            # Compute decay-weighted news velocity over recent stories
            decay_intensity = 1.0  # Current story weight
            decay_lambda = math.log(2) / (self.decay_halflife_hours * 3600)

            four_hour_count = 1
            for prev_story in recent_stories:
                age_secs = (timestamp - prev_story.timestamp).total_seconds()
                decay_intensity += math.exp(-decay_lambda * max(0.0, age_secs))
                if age_secs <= (4 * 3600):
                    four_hour_count += 1

            is_burst = four_hour_count >= self.burst_threshold_count

        # Append new story to history
        history.append(
            StoryClusterRecord(
                story_id=story_id,
                ticker=ticker,
                headline=headline,
                timestamp=timestamp,
                source=source,
                content_hash=content_hash,
                token_set=tokens
            )
        )

        return NoveltyIntensityResult(
            story_id=story_id,
            ticker=ticker,
            is_novel=is_novel,
            novelty_score=round(novelty_score, 3),
            cluster_size_24h=cluster_size,
            source_diversity_count=source_diversity,
            decay_weighted_intensity=round(decay_intensity, 2),
            is_breaking_burst=is_burst
        )
