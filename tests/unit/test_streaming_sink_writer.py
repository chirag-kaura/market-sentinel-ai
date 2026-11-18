"""
Unit Tests for Streaming Persistence Sink Writer
Market Sentinel AI — Phase 4: Step 4.6
"""

from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import pytest

from streaming.sink_writer import StreamingSinkWriter


@pytest.fixture
def temp_parquet_dir(tmp_path):
    return tmp_path / "streaming_parquet"


def test_sink_writer_initialization(temp_parquet_dir):
    writer = StreamingSinkWriter(parquet_base_dir=str(temp_parquet_dir), buffer_size=10)
    assert writer.buffer_size == 10
    assert "news" in writer._buffers
    assert "corporate" in writer._buffers
    assert "spikes" in writer._buffers


def test_sink_writer_buffer_accumulation_and_manual_flush(temp_parquet_dir):
    writer = StreamingSinkWriter(parquet_base_dir=str(temp_parquet_dir), buffer_size=10)

    # Append 3 records (less than buffer_size 10)
    for i in range(3):
        auto_flushed = writer.append_event(
            "news",
            {
                "event_id": f"EVT_{i}",
                "canonical_url": f"https://example.com/news_{i}",
                "title": f"Test Title {i}",
                "published_at_utc": "2026-03-30T10:00:00+00:00",
                "detected_symbols": ["RELIANCE"],
            },
        )
        assert auto_flushed is False

    assert len(writer._buffers["news"]) == 3

    # Explicit flush
    counts = writer.flush()
    assert counts["news"] == 3
    assert len(writer._buffers["news"]) == 0

    # Verify Parquet file was generated
    parquet_files = list(temp_parquet_dir.glob("**/*.parquet"))
    assert len(parquet_files) == 1

    # Read Parquet file back and verify schema
    df_read = pd.read_parquet(parquet_files[0])
    assert len(df_read) == 3
    assert "event_id" in df_read.columns
    assert "canonical_url" in df_read.columns
    assert "RELIANCE" in df_read["detected_symbols"].iloc[0]


def test_sink_writer_auto_flush_on_buffer_capacity(temp_parquet_dir):
    writer = StreamingSinkWriter(parquet_base_dir=str(temp_parquet_dir), buffer_size=3)

    # Append 1st and 2nd record
    assert writer.append_event("spikes", {
        "spike_id": "SPK_1",
        "symbol": "TCS",
        "detected_at_utc": "2026-03-30T11:00:00+00:00",
        "article_count": 4,
    }) is False

    assert writer.append_event("spikes", {
        "spike_id": "SPK_2",
        "symbol": "INFY",
        "detected_at_utc": "2026-03-30T11:05:00+00:00",
        "article_count": 5,
    }) is False

    # 3rd record hits buffer_size=3 -> triggers auto-flush
    assert writer.append_event("spikes", {
        "spike_id": "SPK_3",
        "symbol": "RELIANCE",
        "detected_at_utc": "2026-03-30T11:10:00+00:00",
        "article_count": 3,
    }) is True

    # Buffer should now be empty post-flush
    assert len(writer._buffers["spikes"]) == 0

    parquet_files = list(temp_parquet_dir.glob("spikes/**/*.parquet"))
    assert len(parquet_files) == 1
    df = pd.read_parquet(parquet_files[0])
    assert len(df) == 3
    assert set(df["symbol"].tolist()) == {"TCS", "INFY", "RELIANCE"}


def test_sink_writer_deduplication_on_flush(temp_parquet_dir):
    writer = StreamingSinkWriter(parquet_base_dir=str(temp_parquet_dir), buffer_size=10)

    # Append duplicate event_id
    writer.append_event("corporate", {
        "event_id": "CORP_DUP",
        "symbol": "WIPRO",
        "filing_date_utc": "2026-03-30T12:00:00+00:00",
        "announcement_type": "Board Meeting",
    })
    writer.append_event("corporate", {
        "event_id": "CORP_DUP",
        "symbol": "WIPRO",
        "filing_date_utc": "2026-03-30T12:00:00+00:00",
        "announcement_type": "Board Meeting",
    })

    counts = writer.flush()
    assert counts["corporate"] == 1  # Deduplicated to 1

    parquet_files = list(temp_parquet_dir.glob("corporate/**/*.parquet"))
    assert len(parquet_files) == 1
    df = pd.read_parquet(parquet_files[0])
    assert len(df) == 1
