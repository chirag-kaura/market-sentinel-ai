"""
News & Corporate Disclosures Feature Engineering Pipeline (Phase 5 — Step 5.4)
Market Sentinel AI — Quantitative Text Feature Store

Transforms unstructured news and corporate disclosures into symbol-aligned daily features:
- Multi-day news intensity counts (1d, 3d, 7d).
- Symbol-relative news velocity Z-scores (30-day baseline).
- Corporate announcement category binary flags (earnings, board meeting, M&A).
- Lexicon-based sentiment polarity proxies (bounded [-1.0, +1.0]).
- Strict post-market rollover logic: articles published after 15:30 IST (10:00 UTC)
  are attributed to the next trading day to prevent look-ahead leakage.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("market_sentinel.processing.features.news_features")
logger.setLevel(logging.INFO)

# Lightweight Loughran-McDonald inspired financial sentiment lexicon
POSITIVE_TERMS = {
    "profit", "growth", "jump", "surge", "beats", "record", "gain", "dividend",
    "expansion", "upgrade", "outperform", "bullish", "approval", "strong", "win",
    "secured", "positive", "collaborate", "partnership", "soar", "rallies"
}

NEGATIVE_TERMS = {
    "loss", "fall", "drop", "plunge", "decline", "miss", "fraud", "investigation",
    "probe", "penalty", "default", "scam", "downgrade", "bearish", "weak", "slump",
    "deficit", "litigation", "fine", "cut", "warning", "breach", "crash"
}


class NewsFeatureExtractor:
    """
    Extracts daily quantitative features from financial news streams and filings.
    """

    # 15:30 IST = 10:00 UTC
    MARKET_CLOSE_UTC_HOUR = 10
    MARKET_CLOSE_UTC_MINUTE = 0

    @classmethod
    def attribute_to_trading_date(cls, published_at: datetime) -> date:
        """
        Attributes article to appropriate trading date.
        If published strictly after 10:00 UTC (15:30 IST), rolls over to next calendar day.
        """
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        else:
            published_at = published_at.astimezone(timezone.utc)

        # Check if past 10:00 UTC
        cutoff = published_at.replace(
            hour=cls.MARKET_CLOSE_UTC_HOUR,
            minute=cls.MARKET_CLOSE_UTC_MINUTE,
            second=0,
            microsecond=0,
        )

        if published_at > cutoff:
            return (published_at + timedelta(days=1)).date()
        return published_at.date()

    @staticmethod
    def calculate_text_sentiment(text: str) -> float:
        """
        Computes lexicon-based polarity in [-1.0, +1.0].
        Returns 0.0 if neutral or empty.
        """
        if not text:
            return 0.0

        tokens = set(re.findall(r"\b[a-zA-Z]{3,}\b", text.lower()))
        pos_count = len(tokens.intersection(POSITIVE_TERMS))
        neg_count = len(tokens.intersection(NEGATIVE_TERMS))
        total = pos_count + neg_count

        if total == 0:
            return 0.0
        return (pos_count - neg_count) / float(total)

    @classmethod
    def extract_daily_news_features(
        cls,
        news_articles: List[Dict[str, Any]],
        corporate_disclosures: Optional[List[Dict[str, Any]]] = None,
        date_range: Optional[List[date]] = None,
        symbols: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Aggregates news and corporate disclosures into a daily feature matrix indexed by (symbol, trade_date).
        """
        corporate_disclosures = corporate_disclosures or []
        records = []

        # Process news articles
        for art in news_articles:
            pub_raw = art.get("published_at_utc")
            if isinstance(pub_raw, str):
                try:
                    dt = datetime.fromisoformat(pub_raw.replace("Z", "+00:00"))
                except ValueError:
                    continue
            elif isinstance(pub_raw, datetime):
                dt = pub_raw
            else:
                continue

            target_date = cls.attribute_to_trading_date(dt)
            headline = art.get("title", "")
            summary = art.get("summary") or ""
            full_text = f"{headline} {summary}"
            sentiment = cls.calculate_text_sentiment(full_text)

            detected_syms = art.get("detected_symbols") or []
            for sym in detected_syms:
                records.append({
                    "symbol": sym.strip().upper(),
                    "trade_date": target_date,
                    "is_news": 1,
                    "is_disclosure": 0,
                    "sentiment": sentiment,
                    "has_financial_results": 0,
                    "has_board_meeting": 0,
                    "has_mna": 0,
                    "has_compliance": 0,
                })

        # Process corporate disclosures
        for disc in corporate_disclosures:
            filing_raw = disc.get("filing_date_utc") or disc.get("published_at_utc")
            if isinstance(filing_raw, str):
                try:
                    dt = datetime.fromisoformat(filing_raw.replace("Z", "+00:00"))
                except ValueError:
                    continue
            elif isinstance(filing_raw, datetime):
                dt = filing_raw
            else:
                continue

            target_date = cls.attribute_to_trading_date(dt)
            sym = disc.get("symbol", "").strip().upper()
            if not sym:
                continue

            cat = (disc.get("announcement_type") or disc.get("category") or "").lower()

            records.append({
                "symbol": sym,
                "trade_date": target_date,
                "is_news": 0,
                "is_disclosure": 1,
                "sentiment": 0.0,
                "has_financial_results": 1 if any(w in cat for w in ["result", "financial", "earnings"]) else 0,
                "has_board_meeting": 1 if "board" in cat else 0,
                "has_mna": 1 if any(w in cat for w in ["acquisition", "merger", "amalgamation"]) else 0,
                "has_compliance": 1 if any(w in cat for w in ["insider", "pit", "penalty", "action"]) else 0,
            })

        if not records:
            return pd.DataFrame()

        raw_df = pd.DataFrame(records)

        # Aggregate per (symbol, trade_date)
        daily_agg = (
            raw_df.groupby(["symbol", "trade_date"])
            .agg(
                news_count_1d=("is_news", "sum"),
                disclosure_count_1d=("is_disclosure", "sum"),
                avg_sentiment_polarity_1d=("sentiment", "mean"),
                has_financial_results=("has_financial_results", "max"),
                has_board_meeting=("has_board_meeting", "max"),
                has_mna_filing=("has_mna", "max"),
                has_compliance_action=("has_compliance", "max"),
            )
            .reset_index()
        )

        # Compute rolling window metrics per symbol
        output_dfs = []
        for sym, group in daily_agg.groupby("symbol"):
            g = group.sort_values("trade_date").copy()
            # 3d and 7d rolling sum of news
            g["news_count_3d"] = g["news_count_1d"].rolling(window=3, min_periods=1).sum()
            g["news_count_7d"] = g["news_count_1d"].rolling(window=7, min_periods=1).sum()

            # 30-day baseline news velocity Z-score
            news_mean_30d = g["news_count_1d"].rolling(window=30, min_periods=3).mean()
            news_std_30d = g["news_count_1d"].rolling(window=30, min_periods=3).std().fillna(1.0)
            g["news_velocity_zscore_30d"] = (g["news_count_1d"] - news_mean_30d) / news_std_30d.replace(0, 1.0)

            # Round metrics
            g["avg_sentiment_polarity_1d"] = g["avg_sentiment_polarity_1d"].round(4)
            g["news_velocity_zscore_30d"] = g["news_velocity_zscore_30d"].round(4)
            output_dfs.append(g)

        if not output_dfs:
            return pd.DataFrame()

        final_df = pd.concat(output_dfs, ignore_index=True)
        return final_df.sort_values(["symbol", "trade_date"]).reset_index(drop=True)
