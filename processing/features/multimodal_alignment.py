"""
Multimodal Market-News Feature Alignment Engine (Phase 5 — Step 5.5)
Market Sentinel AI — Cross-Modal Feature Store

Aligns structured daily market metrics (Step 5.2) with news/disclosure features (Step 5.4)
along composite key (symbol, trade_date). Imputes non-news days with neutral priors
and computes cross-modal surveillance interaction features:
- news_price_divergence: High price move with low or zero news.
- volume_news_divergence: Abnormal volume Z-score without corresponding news velocity.
- sentiment_return_alignment: Directional coherence between sentiment and 1d return.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("market_sentinel.processing.features.multimodal_alignment")
logger.setLevel(logging.INFO)


class MultimodalFeatureAligner:
    """
    Joins market and news features and computes cross-modal interaction indicators.
    """

    DEFAULT_NEWS_FILLS = {
        "news_count_1d": 0,
        "disclosure_count_1d": 0,
        "avg_sentiment_polarity_1d": 0.0,
        "has_financial_results": 0,
        "has_board_meeting": 0,
        "has_mna_filing": 0,
        "has_compliance_action": 0,
        "news_count_3d": 0,
        "news_count_7d": 0,
        "news_velocity_zscore_30d": 0.0,
    }

    @classmethod
    def align_features(
        cls,
        market_df: pd.DataFrame,
        news_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Performs left-outer join of market time series with news features on (symbol, trade_date).
        Computes cross-modal interaction features.
        """
        if market_df.empty:
            return pd.DataFrame()

        # Enforce copy and ensure trade_date is date object or string formatted consistently
        aligned = market_df.copy()
        aligned["trade_date"] = pd.to_datetime(aligned["trade_date"]).dt.date
        aligned["symbol"] = aligned["symbol"].astype(str).str.strip().str.upper()

        if news_df is not None and not news_df.empty:
            n_df = news_df.copy()
            n_df["trade_date"] = pd.to_datetime(n_df["trade_date"]).dt.date
            n_df["symbol"] = n_df["symbol"].astype(str).str.strip().str.upper()

            # Merge on (symbol, trade_date)
            aligned = pd.merge(
                aligned,
                n_df,
                on=["symbol", "trade_date"],
                how="left",
            )
        else:
            # If no news provided, create columns with default fills
            for col, default_val in cls.DEFAULT_NEWS_FILLS.items():
                aligned[col] = default_val

        # Fill missing news values for trading days where no news was published
        for col, default_val in cls.DEFAULT_NEWS_FILLS.items():
            if col in aligned.columns:
                aligned[col] = aligned[col].fillna(default_val)
            else:
                aligned[col] = default_val

        # -------------------------------------------------------------
        # Compute Cross-Modal Surveillance Indicators
        # -------------------------------------------------------------

        # 1. News-Price Divergence: |Return_1d| / (ln(news_count_1d + 1) + 1)
        # Large value = large price move on zero or low news (Suspicious / Unannounced move)
        abs_ret = aligned["log_return_1d"].abs().fillna(0.0)
        news_count_smooth = np.log1p(aligned["news_count_1d"].astype(float)) + 1.0
        aligned["news_price_divergence"] = (abs_ret / news_count_smooth).round(6)

        # 2. Volume-News Divergence: Volume Z-Score - News Velocity Z-Score
        # Large positive value = high abnormal volume without corresponding news velocity
        vol_z = aligned.get("volume_zscore_20d", pd.Series(0.0, index=aligned.index)).fillna(0.0)
        news_z = aligned["news_velocity_zscore_30d"].fillna(0.0)
        aligned["volume_news_divergence"] = (vol_z - news_z).round(4)

        # 3. Sentiment-Return Alignment: sign(return_1d) * sign(sentiment_1d)
        # +1 = Coherent (e.g. positive news + positive return)
        # -1 = Inverted (e.g. positive news + negative return, or negative news + pump)
        #  0 = Neutral (either zero return or zero sentiment)
        ret_sign = np.sign(aligned["log_return_1d"].fillna(0.0))
        sent_sign = np.sign(aligned["avg_sentiment_polarity_1d"].fillna(0.0))
        aligned["sentiment_return_alignment"] = (ret_sign * sent_sign).astype(int)

        # 4. Abnormal Unbacked Movement Flag (Binary Indicator)
        # Triggered when |1d return| > 3% or volume_z > 2.5 in total absence of news
        is_high_move = (abs_ret > 0.03) | (vol_z > 2.5)
        is_news_vacuum = (aligned["news_count_1d"] == 0) & (aligned["disclosure_count_1d"] == 0)
        aligned["is_unbacked_market_move"] = (is_high_move & is_news_vacuum).astype(int)

        return aligned.sort_values(["symbol", "trade_date"]).reset_index(drop=True)
