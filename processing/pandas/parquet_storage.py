"""Columnar Parquet Feature and Snapshot Storage Module.

Provides fast, partitioned Snappy-compressed Parquet read and write operations
for analytical feature datasets and historical market archives.
"""
from datetime import date
import logging
import os
from typing import List, Optional
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


class ParquetStorage:
    """Manages reading and writing columnar Parquet time-series datasets."""

    def __init__(self, base_dir: str = "data/features"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def write_features_dataframe(
        self,
        df: pd.DataFrame,
        dataset_name: str = "market_features",
        partition_by_symbol: bool = True
    ) -> str:
        """Write DataFrame to Snappy-compressed Parquet.

        If partition_by_symbol is True, partitions datasets into:
        base_dir/{dataset_name}/symbol=XYZ/data.parquet
        """
        target_path = os.path.join(self.base_dir, dataset_name)
        os.makedirs(target_path, exist_ok=True)

        if partition_by_symbol and "symbol" in df.columns:
            # Partitioned dataset write
            df.to_parquet(
                target_path,
                partition_cols=["symbol"],
                compression="snappy",
                engine="pyarrow",
                index=False,
            )
        else:
            file_path = os.path.join(target_path, "data.parquet")
            df.to_parquet(file_path, compression="snappy", engine="pyarrow", index=False)
            target_path = file_path

        logger.info("Successfully wrote %d rows to %s", len(df), target_path)
        return target_path

    def read_features(
        self,
        dataset_name: str = "market_features",
        symbols: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Read Parquet dataset with optional symbol and date filtering."""
        target_path = os.path.join(self.base_dir, dataset_name)
        if not os.path.exists(target_path):
            return pd.DataFrame()

        # Load dataset
        filters = []
        if symbols:
            filters.append(("symbol", "in", symbols))

        dataset = pq.ParquetDataset(target_path, filters=filters if filters else None)
        df = dataset.read_pandas().to_pandas()

        if "trade_date" in df.columns:
            df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
            if start_date:
                df = df[df["trade_date"] >= start_date]
            if end_date:
                df = df[df["trade_date"] <= end_date]

        return df.sort_values(by=["symbol", "trade_date"] if "trade_date" in df.columns else ["symbol"]).reset_index(drop=True)
