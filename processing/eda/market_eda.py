"""
Financial Market Exploratory Data Analysis (EDA) Engine
Market Sentinel AI — Phase 5: Step 5.1

Provides comprehensive statistical profiling for equity market time series:
- Log returns, rolling volatility, skewness, excess kurtosis.
- Jarque-Bera normality tests for fat-tail characterization.
- Volume & delivery liquidity distributions.
- Volatility clustering indicators (autocorrelation of squared returns).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger("market_sentinel.processing.eda.market_eda")
logger.setLevel(logging.INFO)


@dataclass
class MarketSeriesProfile:
    symbol: str
    record_count: int
    start_date: str
    end_date: str
    mean_daily_return: float
    std_daily_return: float
    annualized_volatility: float
    skewness: float
    excess_kurtosis: float
    is_normal_distribution: bool
    jarque_bera_stat: float
    jarque_bera_pvalue: float
    avg_turnover_cr: float
    avg_delivery_pct: float
    volatility_clustering_detected: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "record_count": self.record_count,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "mean_daily_return": round(self.mean_daily_return, 6),
            "std_daily_return": round(self.std_daily_return, 6),
            "annualized_volatility": round(self.annualized_volatility, 4),
            "skewness": round(self.skewness, 4),
            "excess_kurtosis": round(self.excess_kurtosis, 4),
            "is_normal_distribution": self.is_normal_distribution,
            "jarque_bera_stat": round(self.jarque_bera_stat, 2),
            "jarque_bera_pvalue": round(self.jarque_bera_pvalue, 6),
            "avg_turnover_cr": round(self.avg_turnover_cr, 2),
            "avg_delivery_pct": round(self.avg_delivery_pct, 4),
            "volatility_clustering_detected": self.volatility_clustering_detected,
        }


class MarketEDAProfiler:
    """
    Computes statistical profiles, distributional moments, and stylized facts
    from historical equity Bhavcopy and MTO delivery data.
    """

    @staticmethod
    def compute_log_returns(df: pd.DataFrame, price_col: str = "close_price") -> pd.Series:
        """
        Computes backward-looking log returns: r_t = ln(P_t / P_{t-1}).
        Guarantees zero look-ahead bias.
        """
        if df.empty or len(df) < 2:
            return pd.Series(dtype=float)
        
        # Ensure chronological ordering
        df_sorted = df.sort_values("trade_date")
        log_ret = np.log(df_sorted[price_col] / df_sorted[price_col].shift(1))
        return log_ret.dropna()

    @staticmethod
    def profile_symbol_series(
        symbol: str,
        df: pd.DataFrame,
        price_col: str = "close_price",
        turnover_col: str = "total_turnover",
        delivery_pct_col: str = "delivery_to_traded_ratio",
    ) -> MarketSeriesProfile:
        """
        Computes comprehensive distributional metrics and test statistics for a single symbol.
        """
        if df.empty:
            raise ValueError(f"Dataframe for symbol {symbol} is empty.")

        df_sorted = df.sort_values("trade_date").copy()
        record_count = len(df_sorted)
        start_date = str(df_sorted["trade_date"].min())
        end_date = str(df_sorted["trade_date"].max())

        # Compute log returns
        log_returns = MarketEDAProfiler.compute_log_returns(df_sorted, price_col=price_col)

        if len(log_returns) < 3:
            return MarketSeriesProfile(
                symbol=symbol,
                record_count=record_count,
                start_date=start_date,
                end_date=end_date,
                mean_daily_return=0.0,
                std_daily_return=0.0,
                annualized_volatility=0.0,
                skewness=0.0,
                excess_kurtosis=0.0,
                is_normal_distribution=False,
                jarque_bera_stat=0.0,
                jarque_bera_pvalue=1.0,
                avg_turnover_cr=0.0,
                avg_delivery_pct=0.0,
                volatility_clustering_detected=False,
            )

        mean_ret = float(log_returns.mean())
        std_ret = float(log_returns.std())
        ann_vol = float(std_ret * np.sqrt(252))  # Standard 252 trading days

        skew = float(stats.skew(log_returns))
        kurt = float(stats.kurtosis(log_returns, fisher=True))  # Fisher kurtosis (normal == 0)

        # Jarque-Bera test for normality
        jb_stat, jb_pval = stats.jarque_bera(log_returns)
        is_normal = bool(jb_pval > 0.05)

        # Average turnover (convert INR to Crores: 1 Cr = 1e7)
        if turnover_col in df_sorted.columns:
            avg_turnover_cr = float((df_sorted[turnover_col].mean()) / 1e7)
        else:
            avg_turnover_cr = 0.0

        # Average delivery percentage
        if delivery_pct_col in df_sorted.columns:
            avg_deliv = float(df_sorted[delivery_pct_col].mean())
        else:
            avg_deliv = 0.0

        # Volatility clustering test: check lag-1 autocorrelation of squared returns
        squared_returns = log_returns**2
        if len(squared_returns) > 5:
            autocorr_sq = float(squared_returns.autocorr(lag=1))
            vol_clustering = bool(autocorr_sq > 0.10)
        else:
            vol_clustering = False

        return MarketSeriesProfile(
            symbol=symbol,
            record_count=record_count,
            start_date=start_date,
            end_date=end_date,
            mean_daily_return=mean_ret,
            std_daily_return=std_ret,
            annualized_volatility=ann_vol,
            skewness=skew,
            excess_kurtosis=kurt,
            is_normal_distribution=is_normal,
            jarque_bera_stat=float(jb_stat),
            jarque_bera_pvalue=float(jb_pval),
            avg_turnover_cr=avg_turnover_cr,
            avg_delivery_pct=avg_deliv,
            volatility_clustering_detected=vol_clustering,
        )

    @staticmethod
    def generate_eda_summary_table(profiles: List[MarketSeriesProfile]) -> pd.DataFrame:
        """
        Combines individual profiles into a consolidated summary dataframe.
        """
        rows = [p.to_dict() for p in profiles]
        return pd.DataFrame(rows)
