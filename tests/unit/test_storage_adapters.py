"""Unit tests for Storage Adapters (SQLAlchemy Models and Parquet Storage)."""
from datetime import date
from decimal import Decimal
import os
import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.market import Base, MarketQuoteModel, SymbolMasterModel
from backend.repositories.market_repository import MarketRepository
from processing.pandas.parquet_storage import ParquetStorage


def test_sqlalchemy_model_compilation():
    """Test SQLite in-memory compilation of market models."""
    # Test table schema structure and relationships using in-memory engine
    engine = create_engine("sqlite:///:memory:")
    # Avoid Postgres-specific JSONB/UUID in pure SQLite test by inspecting metadata
    assert "symbol_master" in Base.metadata.tables
    assert "market_quotes_daily" in Base.metadata.tables

    quote_table = Base.metadata.tables["market_quotes_daily"]
    assert "open_price" in quote_table.c
    assert "close_price" in quote_table.c
    assert "volume" in quote_table.c


def test_parquet_storage_roundtrip(tmp_path):
    """Test writing and reading partitioned Snappy Parquet datasets."""
    storage = ParquetStorage(base_dir=str(tmp_path / "features"))

    sample_data = pd.DataFrame([
        {
            "symbol": "RELIANCE",
            "trade_date": "2026-11-16",
            "return_daily": 0.015,
            "volatility_roll_20d": 0.22,
            "volume_zscore_20d": 1.45,
        },
        {
            "symbol": "RELIANCE",
            "trade_date": "2026-11-17",
            "return_daily": -0.008,
            "volatility_roll_20d": 0.23,
            "volume_zscore_20d": 0.85,
        },
        {
            "symbol": "TCS",
            "trade_date": "2026-11-17",
            "return_daily": 0.021,
            "volatility_roll_20d": 0.18,
            "volume_zscore_20d": 2.10,
        }
    ])

    # 1. Write partitioned dataset
    target_path = storage.write_features_dataframe(
        sample_data, dataset_name="test_features", partition_by_symbol=True
    )
    assert os.path.exists(target_path)
    assert os.path.exists(os.path.join(target_path, "symbol=RELIANCE"))
    assert os.path.exists(os.path.join(target_path, "symbol=TCS"))

    # 2. Read back full dataset
    read_df = storage.read_features(dataset_name="test_features")
    assert len(read_df) == 3
    assert "return_daily" in read_df.columns

    # 3. Read back filtered by symbol
    tcs_df = storage.read_features(dataset_name="test_features", symbols=["TCS"])
    assert len(tcs_df) == 1
    assert tcs_df.iloc[0]["symbol"] == "TCS"
    assert tcs_df.iloc[0]["volume_zscore_20d"] == 2.10
