"""
Integration & Fault Tolerance Tests for Streaming Pipeline (Phase 4 — Step 4.7)
Market Sentinel AI — Event Streaming & Resilience Verification

Validates:
1. Poison-pill isolation & DLQ routing without pipeline crash.
2. Consumer crash & stream replay idempotency (zero duplicate records).
3. High-throughput burst buffering and automatic window flushing.
4. Full End-to-End Streaming Lifecycle:
   Producer -> Schema Validator -> Spike Detection Engine -> Partitioned Sink Writer.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import pandas as pd
import pytest

from processing.spark.news_spike_stream import NewsSpikeStreamEngine
from streaming.consumers.news_event_consumer import NewsEventConsumer
from streaming.producers.news_event_producer import NewsEventProducer
from streaming.sink_writer import StreamingSinkWriter


@pytest.fixture
def streaming_env(tmp_path):
    parquet_dir = tmp_path / "streaming_parquet"
    dlq_dir = tmp_path / "dlq"
    dlq_dir.mkdir(parents=True, exist_ok=True)
    dlq_file = dlq_dir / "quarantine.jsonl"
    return {
        "parquet_dir": str(parquet_dir),
        "dlq_file": str(dlq_file),
    }


def test_streaming_poison_pill_isolation_and_dlq(streaming_env):
    """
    Ensures corrupt or malformed streaming payloads are isolated to DLQ
    while valid events continue downstream to persistent storage.
    """
    consumer = NewsEventConsumer(
        dlq_file=streaming_env["dlq_file"],
        mock_mode=True,
    )
    sink_writer = StreamingSinkWriter(
        parquet_base_dir=streaming_env["parquet_dir"],
        buffer_size=10,
    )

    mixed_messages = [
        # Valid message 1
        {
            "event_id": "EVT_VALID_01",
            "canonical_url": "https://example.com/rel_1",
            "title": "Reliance Q4 profit beats estimates",
            "source_outlet": "Economic Times",
            "published_at_utc": "2026-03-30T10:00:00+00:00",
            "ingested_at_utc": "2026-03-30T10:05:00+00:00",
            "detected_symbols": ["RELIANCE"],
            "headline_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
        },
        # Poison pill 1: Corrupted missing required fields (missing published_at_utc, canonical_url)
        {
            "event_id": "EVT_POISON_01",
            "title": "Malformed data payload with missing keys",
        },
        # Poison pill 2: Invalid data type for symbols
        {
            "event_id": "EVT_POISON_02",
            "canonical_url": "https://example.com/bad_sym",
            "title": "Bad symbol data",
            "source_outlet": "Economic Times",
            "published_at_utc": "2026-03-30T10:05:00+00:00",
            "ingested_at_utc": "2026-03-30T10:05:00+00:00",
            "detected_symbols": "NOT_AN_ARRAY",
            "headline_hash": "11223344556611223344556611223344",
        },
        # Valid message 2
        {
            "event_id": "EVT_VALID_02",
            "canonical_url": "https://example.com/rel_2",
            "title": "Reliance green energy rollout advances",
            "source_outlet": "Moneycontrol",
            "published_at_utc": "2026-03-30T10:10:00+00:00",
            "ingested_at_utc": "2026-03-30T10:15:00+00:00",
            "detected_symbols": ["RELIANCE"],
            "headline_hash": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5",
        },
    ]

    processed_valid = []
    for raw in mixed_messages:
        # Simulate consumer validation
        record = consumer.process_message(raw)
        if record is not None:
            processed_valid.append(record)
            sink_writer.append_event("news", record)

    # Flush valid records
    counts = sink_writer.flush()

    # 1. Pipeline did not crash and processed exactly 2 valid records
    assert len(processed_valid) == 2
    assert counts["news"] == 2

    # 2. DLQ received exactly 2 quarantine records
    assert Path(streaming_env["dlq_file"]).exists()
    with open(streaming_env["dlq_file"], "r", encoding="utf-8") as f:
        quarantine_lines = [json.loads(line) for line in f if line.strip()]
    assert len(quarantine_lines) == 2
    assert quarantine_lines[0]["raw_payload"]["event_id"] == "EVT_POISON_01"
    assert quarantine_lines[1]["raw_payload"]["event_id"] == "EVT_POISON_02"


def test_streaming_crash_and_replay_idempotency(streaming_env):
    """
    Simulates a consumer restart / stream replay where the exact same batch
    is re-delivered. The sink writer must deduplicate records idempotently.
    """
    sink_writer = StreamingSinkWriter(
        parquet_base_dir=streaming_env["parquet_dir"],
        buffer_size=10,
    )

    batch_event = {
        "event_id": "EVT_REPLAY_100",
        "canonical_url": "https://example.com/tcs_result",
        "title": "TCS announces record dividend",
        "published_at_utc": "2026-03-30T11:00:00+00:00",
        "detected_symbols": ["TCS"],
    }

    # First delivery
    sink_writer.append_event("news", batch_event)
    # Crash / Replay: same event appended again
    sink_writer.append_event("news", batch_event)

    flush_counts = sink_writer.flush()
    # In-batch deduplication guarantees only 1 row is written
    assert flush_counts["news"] == 1

    # Verify Parquet file contents
    parquet_files = list(Path(streaming_env["parquet_dir"]).glob("news/**/*.parquet"))
    assert len(parquet_files) == 1
    df = pd.read_parquet(parquet_files[0])
    assert len(df) == 1
    assert df["event_id"].iloc[0] == "EVT_REPLAY_100"


def test_streaming_high_throughput_burst_and_auto_flush(streaming_env):
    """
    Tests high-volume event bursts across multiple symbols, verifying
    buffer capacity triggering automatic flushes without memory leaks.
    """
    sink_writer = StreamingSinkWriter(
        parquet_base_dir=streaming_env["parquet_dir"],
        buffer_size=15,  # Trigger auto-flush every 15 items
    )

    symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
    total_events = 45  # 45 items should trigger exactly 3 auto-flushes

    auto_flush_count = 0
    for i in range(total_events):
        sym = symbols[i % len(symbols)]
        flushed = sink_writer.append_event(
            "news",
            {
                "event_id": f"BURST_{i:04d}",
                "canonical_url": f"https://example.com/burst_{i}",
                "title": f"Market bulletin {i} for {sym}",
                "published_at_utc": "2026-03-30T12:00:00+00:00",
                "detected_symbols": [sym],
            },
        )
        if flushed:
            auto_flush_count += 1

    assert auto_flush_count == 3
    assert len(sink_writer._buffers["news"]) == 0

    parquet_files = list(Path(streaming_env["parquet_dir"]).glob("news/**/*.parquet"))
    assert len(parquet_files) == 3


def test_full_streaming_lifecycle_end_to_end(streaming_env):
    """
    Validates complete streaming lifecycle:
    1. Producer serializes raw news into schema-compliant streaming payloads.
    2. Spark/Pandas Window Spike Stream computes 1-hour event-time velocity.
    3. Detected news intensity spikes are generated.
    4. Both raw events and spike alerts are persisted to partitioned Parquet storage.
    """
    producer = NewsEventProducer(mock_mode=True)
    spike_engine = NewsSpikeStreamEngine(spike_threshold=3)
    sink_writer = StreamingSinkWriter(
        parquet_base_dir=streaming_env["parquet_dir"],
        buffer_size=20,
    )

    base_time = datetime(2026, 3, 30, 14, 0, 0, tzinfo=timezone.utc)
    raw_articles = [
        {
            "title": "Infosys signs $1B multi-year cloud transformation contract",
            "canonical_url": "https://example.com/infy_contract_1",
            "source_outlet": "Economic Times",
            "published_at_utc": (base_time + timedelta(minutes=5)).isoformat(),
            "summary": "Infosys secures cloud deal.",
        },
        {
            "title": "Infosys collaborates with global retail major",
            "canonical_url": "https://example.com/infy_contract_2",
            "source_outlet": "Moneycontrol",
            "published_at_utc": (base_time + timedelta(minutes=15)).isoformat(),
            "summary": "Expansion of enterprise partnership.",
        },
        {
            "title": "Infosys introduces new generative AI agent framework",
            "canonical_url": "https://example.com/infy_contract_3",
            "source_outlet": "Livemint",
            "published_at_utc": (base_time + timedelta(minutes=25)).isoformat(),
            "summary": "Enterprise AI suite launched.",
        },
    ]

    # Step 1: Producer formats & publishes event
    produced_events = []
    for art in raw_articles:
        evt = producer.publish_news_event(art, detected_symbols=["INFY"])
        produced_events.append(evt)
        # Append raw event to persistent storage
        sink_writer.append_event("news", evt)

    # Step 2: Stream Processor evaluates event window
    spikes = spike_engine.process_micro_batch(
        events=produced_events,
        current_time_utc=base_time + timedelta(minutes=30),
    )

    # INFY has 3 events -> triggers spike alert
    assert len(spikes) == 1
    spike = spikes[0]
    assert spike.symbol == "INFY"
    assert spike.article_count == 3
    assert spike.is_spike is True

    # Step 3: Append detected spike to persistent sink
    sink_writer.append_event("spikes", spike.to_dict())

    # Step 4: Flush all buffers
    counts = sink_writer.flush()
    assert counts["news"] == 3
    assert counts["spikes"] == 1

    # Verify physical storage existence
    news_parquet = list(Path(streaming_env["parquet_dir"]).glob("news/**/*.parquet"))
    spike_parquet = list(Path(streaming_env["parquet_dir"]).glob("spikes/**/*.parquet"))

    assert len(news_parquet) >= 1
    assert len(spike_parquet) >= 1

    # Validate schema of persisted spike
    df_spike = pd.read_parquet(spike_parquet[0])
    assert df_spike["symbol"].iloc[0] == "INFY"
    assert int(df_spike["article_count"].iloc[0]) == 3
    assert bool(df_spike["is_spike"].iloc[0]) is True
