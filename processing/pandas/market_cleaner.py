"""Market Data Cleaning and Normalization Module.

Transforms raw market quote records into clean, validated Pandas DataFrames,
enforcing type conversions, duplicate resolution, price boundary checks,
and structured quality audit logging.
"""
from datetime import date
from decimal import Decimal
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class MarketDataCleaner:
    """Cleans and standardizes raw daily market quote datasets."""

    REQUIRED_COLUMNS = [
        "symbol",
        "trade_date",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "turnover",
    ]

    @classmethod
    def clean_quotes(
        cls,
        records: List[Dict],
        source_provider: str = "SRC-NSE-EOD"
    ) -> Tuple[pd.DataFrame, Dict]:
        """Clean raw market quote records into a standardized DataFrame.

        Returns:
            Tuple of (clean_df, audit_metrics_dict)
        """
        audit_metrics = {
            "initial_rows": len(records),
            "duplicates_removed": 0,
            "corrupted_rows_quarantined": 0,
            "delivery_nulls_imputed": 0,
            "final_clean_rows": 0,
        }

        if not records:
            empty_df = pd.DataFrame(
                columns=cls.REQUIRED_COLUMNS + ["delivery_qty", "delivery_pct", "source_provider"]
            )
            return empty_df, audit_metrics

        df = pd.DataFrame(records)

        # 1. Enforce date standard
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date

        # 2. Convert numeric fields with float precision for analytics
        numeric_cols = ["open_price", "high_price", "low_price", "close_price", "turnover"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype("int64")

        # 3. Handle delivery metrics (may be missing in some raw archives)
        if "delivery_qty" in df.columns:
            df["delivery_qty"] = pd.to_numeric(df["delivery_qty"], errors="coerce")
        else:
            df["delivery_qty"] = None

        if "delivery_pct" in df.columns:
            df["delivery_pct"] = pd.to_numeric(df["delivery_pct"], errors="coerce")
        else:
            df["delivery_pct"] = None

        # 4. Filter invalid price anomalies (high < low, non-positive prices)
        valid_price_mask = (
            (df["open_price"] > 0)
            & (df["close_price"] > 0)
            & (df["low_price"] > 0)
            & (df["high_price"] >= df["low_price"])
            & (df["high_price"] >= df["open_price"])
            & (df["high_price"] >= df["close_price"])
            & (df["low_price"] <= df["open_price"])
            & (df["low_price"] <= df["close_price"])
        )

        invalid_count = int((~valid_price_mask).sum())
        if invalid_count > 0:
            logger.warning("Quarantining %d records with invalid price boundaries", invalid_count)
            audit_metrics["corrupted_rows_quarantined"] = invalid_count
            df = df[valid_price_mask].copy()

        # 5. Deduplicate (symbol, trade_date) keeping latest ingestion
        initial_before_dedup = len(df)
        df = df.drop_duplicates(subset=["symbol", "trade_date"], keep="last").copy()
        audit_metrics["duplicates_removed"] = initial_before_dedup - len(df)

        # 6. Sort chronologically by symbol and date
        df = df.sort_values(by=["symbol", "trade_date"]).reset_index(drop=True)

        # 7. Add source provider tag if missing
        if "source_provider" not in df.columns:
            df["source_provider"] = source_provider

        audit_metrics["final_clean_rows"] = len(df)
        return df, audit_metrics
