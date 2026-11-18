"""
Market Feature Engineering Pipeline (Phase 5 — Step 5.2)
Market Sentinel AI — Quantitative Financial Feature Store

Extracts causal, backward-looking market features from daily Bhavcopy & delivery records:
- Multi-horizon log returns (1d, 5d, 20d).
- Rolling close-to-close volatility (20d annualized).
- Parkinson high-low extreme volatility estimator.
- Rolling volume statistics & volume Z-score (20d baseline).
- Delivery ratio & delivery Z-score (20d baseline).
- 52-week (252-day) high/low price range proximity ratios.
"""

from __future__ import annotations

import logging
from typing import List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("market_sentinel.processing.features.market_features")
logger.setLevel(logging.INFO)


class MarketFeatureExtractor:
    """
    Transforms clean daily market price and volume records into feature matrices.
    Strictly enforces zero look-ahead bias through backward-looking rolling windows.
    """

    REQUIRED_COLUMNS = [
        "symbol",
        "trade_date",
        "close_price",
        "open_price",
        "high_price",
        "low_price",
        "total_traded_quantity",
        "delivery_qty",
    ]

    @staticmethod
    def extract_features_for_symbol(
        df: pd.DataFrame,
        rolling_window: int = 20,
    ) -> pd.DataFrame:
        """
        Computes the complete set of market surveillance features for a single symbol.
        """
        if df.empty:
            return pd.DataFrame()

        # Enforce chronological ordering
        df_feat = df.sort_values("trade_date").copy()

        # 1. Multi-horizon log returns
        df_feat["log_return_1d"] = np.log(df_feat["close_price"] / df_feat["close_price"].shift(1))
        df_feat["log_return_5d"] = np.log(df_feat["close_price"] / df_feat["close_price"].shift(5))
        df_feat["log_return_20d"] = np.log(df_feat["close_price"] / df_feat["close_price"].shift(20))

        # 2. Rolling Close-to-Close Volatility (20-day annualized)
        df_feat["volatility_20d"] = (
            df_feat["log_return_1d"].rolling(window=rolling_window, min_periods=5).std()
            * np.sqrt(252)
        )

        # 3. Parkinson High-Low Volatility (20-day annualized)
        # Formula: sqrt( 1 / (4 * ln(2) * N) * sum( ln(H/L)^2 ) ) * sqrt(252)
        hl_ratio = np.log(df_feat["high_price"] / df_feat["low_price"]) ** 2
        parkinson_sum = hl_ratio.rolling(window=rolling_window, min_periods=5).mean()
        df_feat["parkinson_volatility_20d"] = (
            np.sqrt(parkinson_sum / (4 * np.log(2))) * np.sqrt(252)
        )

        # 4. Volume Dynamics & Volume Z-Scores
        vol_series = df_feat["total_traded_quantity"].astype(float)
        vol_mean_20d = vol_series.rolling(window=rolling_window, min_periods=5).mean()
        vol_std_20d = vol_series.rolling(window=rolling_window, min_periods=5).std().replace(0, np.nan)
        df_feat["volume_mean_20d"] = vol_mean_20d
        df_feat["volume_zscore_20d"] = (vol_series - vol_mean_20d) / vol_std_20d

        # 5. Delivery Dynamics & Delivery Z-Scores
        deliv_qty = df_feat["delivery_qty"].astype(float)
        # Avoid division by zero
        df_feat["delivery_ratio"] = (deliv_qty / vol_series.replace(0, np.nan)).clip(0.0, 1.0)
        deliv_mean_20d = df_feat["delivery_ratio"].rolling(window=rolling_window, min_periods=5).mean()
        deliv_std_20d = df_feat["delivery_ratio"].rolling(window=rolling_window, min_periods=5).std().replace(0, np.nan)
        df_feat["delivery_ratio_zscore_20d"] = (df_feat["delivery_ratio"] - deliv_mean_20d) / deliv_std_20d

        # 6. Proximity to 52-week High and Low (252 trading days)
        rolling_high_252 = df_feat["high_price"].rolling(window=252, min_periods=10).max()
        rolling_low_252 = df_feat["low_price"].rolling(window=252, min_periods=10).min()
        df_feat["proximity_to_52w_high"] = df_feat["close_price"] / rolling_high_252
        df_feat["proximity_to_52w_low"] = df_feat["close_price"] / rolling_low_252

        # Replace infinite values and round floats for stability
        df_feat.replace([np.inf, -np.inf], np.nan, inplace=True)
        return df_feat

    @classmethod
    def extract_features_bulk(
        cls,
        df: pd.DataFrame,
        rolling_window: int = 20,
    ) -> pd.DataFrame:
        """
        Extracts market surveillance features across multiple symbols in a bulk dataframe.
        """
        if df.empty or "symbol" not in df.columns:
            return pd.DataFrame()

        processed_dfs: List[pd.DataFrame] = []
        for sym, group in df.groupby("symbol"):
            sym_features = cls.extract_features_for_symbol(group, rolling_window=rolling_window)
            processed_dfs.append(sym_features)

        if not processed_dfs:
            return pd.DataFrame()

        return pd.concat(processed_dfs, ignore_index=True)
