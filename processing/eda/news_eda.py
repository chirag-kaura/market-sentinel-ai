"""
News & Corporate Disclosures Exploratory Data Analysis (EDA) Engine
Market Sentinel AI — Phase 5: Step 5.3

Profiles unstructured text and regulatory disclosure dynamics:
- Temporal publication patterns (market-hours vs pre/post-market vs weekends).
- Symbol coverage skew and multi-entity co-occurrence.
- Announcement category distributions (results, dividends, mergers, board meetings).
- Inter-arrival time distributions and arrival burstiness.
- Headline and summary length characteristics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("market_sentinel.processing.eda.news_eda")
logger.setLevel(logging.INFO)


@dataclass
class NewsDistributionProfile:
    total_articles: int
    unique_symbols_covered: int
    top_covered_symbols: Dict[str, int]
    market_hours_article_pct: float
    weekend_article_pct: float
    avg_headline_words: float
    avg_summary_words: float
    avg_inter_arrival_minutes: float
    median_inter_arrival_minutes: float
    p95_inter_arrival_minutes: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_articles": self.total_articles,
            "unique_symbols_covered": self.unique_symbols_covered,
            "top_covered_symbols": self.top_covered_symbols,
            "market_hours_article_pct": round(self.market_hours_article_pct, 4),
            "weekend_article_pct": round(self.weekend_article_pct, 4),
            "avg_headline_words": round(self.avg_headline_words, 2),
            "avg_summary_words": round(self.avg_summary_words, 2),
            "avg_inter_arrival_minutes": round(self.avg_inter_arrival_minutes, 2),
            "median_inter_arrival_minutes": round(self.median_inter_arrival_minutes, 2),
            "p95_inter_arrival_minutes": round(self.p95_inter_arrival_minutes, 2),
        }


class NewsDisclosureEDAProfiler:
    """
    Statistical profiler for financial news streams and official corporate filings.
    """

    # NSE Trading Hours in IST: 09:15 to 15:30 IST -> UTC: 03:45 to 10:00 UTC
    MARKET_OPEN_UTC_MINUTES = 3 * 60 + 45  # 03:45 UTC = 225 mins
    MARKET_CLOSE_UTC_MINUTES = 10 * 60     # 10:00 UTC = 600 mins

    @staticmethod
    def is_market_hours_utc(dt: datetime) -> bool:
        """
        Returns True if UTC datetime falls within NSE market trading hours (09:15 - 15:30 IST)
        on a weekday (Monday=0 to Friday=4).
        """
        if dt.weekday() >= 5:  # Saturday or Sunday
            return False
        minute_of_day = dt.hour * 60 + dt.minute
        return NewsDisclosureEDAProfiler.MARKET_OPEN_UTC_MINUTES <= minute_of_day <= NewsDisclosureEDAProfiler.MARKET_CLOSE_UTC_MINUTES

    @classmethod
    def profile_news_corpus(
        cls,
        articles: List[Dict[str, Any]],
    ) -> NewsDistributionProfile:
        """
        Profiles a corpus of news articles.
        """
        if not articles:
            return NewsDistributionProfile(
                total_articles=0,
                unique_symbols_covered=0,
                top_covered_symbols={},
                market_hours_article_pct=0.0,
                weekend_article_pct=0.0,
                avg_headline_words=0.0,
                avg_summary_words=0.0,
                avg_inter_arrival_minutes=0.0,
                median_inter_arrival_minutes=0.0,
                p95_inter_arrival_minutes=0.0,
            )

        symbol_counts: Dict[str, int] = {}
        market_hours_count = 0
        weekend_count = 0
        headline_word_lengths: List[int] = []
        summary_word_lengths: List[int] = []
        parsed_timestamps: List[datetime] = []

        for art in articles:
            # Word counts
            title = art.get("title", "")
            summary = art.get("summary") or ""
            headline_word_lengths.append(len(title.split()))
            summary_word_lengths.append(len(summary.split()))

            # Symbol counts
            syms = art.get("detected_symbols") or []
            for s in syms:
                s_clean = s.strip().upper()
                symbol_counts[s_clean] = symbol_counts.get(s_clean, 0) + 1

            # Timestamp parsing
            pub_val = art.get("published_at_utc")
            if isinstance(pub_val, str):
                try:
                    dt = datetime.fromisoformat(pub_val.replace("Z", "+00:00"))
                except ValueError:
                    continue
            elif isinstance(pub_val, datetime):
                dt = pub_val
            else:
                continue

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)

            parsed_timestamps.append(dt)
            if cls.is_market_hours_utc(dt):
                market_hours_count += 1
            if dt.weekday() >= 5:
                weekend_count += 1

        total = len(articles)
        mkt_pct = market_hours_count / total if total > 0 else 0.0
        wknd_pct = weekend_count / total if total > 0 else 0.0

        avg_hl_words = float(np.mean(headline_word_lengths)) if headline_word_lengths else 0.0
        avg_sum_words = float(np.mean(summary_word_lengths)) if summary_word_lengths else 0.0

        # Inter-arrival times
        if len(parsed_timestamps) > 1:
            sorted_times = sorted(parsed_timestamps)
            deltas = [
                (t2 - t1).total_seconds() / 60.0
                for t1, t2 in zip(sorted_times[:-1], sorted_times[1:])
            ]
            avg_ia = float(np.mean(deltas))
            med_ia = float(np.median(deltas))
            p95_ia = float(np.percentile(deltas, 95))
        else:
            avg_ia = 0.0
            med_ia = 0.0
            p95_ia = 0.0

        top_symbols = dict(sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:10])

        return NewsDistributionProfile(
            total_articles=total,
            unique_symbols_covered=len(symbol_counts),
            top_covered_symbols=top_symbols,
            market_hours_article_pct=mkt_pct,
            weekend_article_pct=wknd_pct,
            avg_headline_words=avg_hl_words,
            avg_summary_words=avg_sum_words,
            avg_inter_arrival_minutes=avg_ia,
            median_inter_arrival_minutes=med_ia,
            p95_inter_arrival_minutes=p95_ia,
        )

    @staticmethod
    def profile_corporate_disclosures(disclosures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Profiles corporate regulatory announcement categories and filing timings.
        """
        if not disclosures:
            return {"total_filings": 0, "categories": {}, "top_symbols": {}}

        category_counts: Dict[str, int] = {}
        symbol_counts: Dict[str, int] = {}

        for disc in disclosures:
            cat = disc.get("announcement_type") or disc.get("category") or "General"
            category_counts[cat] = category_counts.get(cat, 0) + 1

            sym = disc.get("symbol")
            if sym:
                sym_clean = sym.strip().upper()
                symbol_counts[sym_clean] = symbol_counts.get(sym_clean, 0) + 1

        return {
            "total_filings": len(disclosures),
            "categories": dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)),
            "top_symbols": dict(sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)),
        }
