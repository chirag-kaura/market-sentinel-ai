"""
Unit Tests for Spark Structured Streaming & News Spike Stream Processor
Market Sentinel AI — Phase 4: Step 4.5
"""

from datetime import datetime, timedelta, timezone
import pytest

from processing.spark.news_spike_stream import NewsSpikeStreamEngine, WindowSpikeResult


def test_news_spike_stream_engine_initialization():
    engine = NewsSpikeStreamEngine(
        bootstrap_servers="localhost:19092",
        input_topic="news.events.raw",
        output_topic="news.intensity.spikes",
        spike_threshold=3,
    )
    assert engine.input_topic == "news.events.raw"
    assert engine.output_topic == "news.intensity.spikes"
    assert engine.spike_threshold == 3


def test_micro_batch_spike_detection_triggers_above_threshold():
    engine = NewsSpikeStreamEngine(spike_threshold=3)
    base_time = datetime(2026, 3, 30, 10, 0, 0, tzinfo=timezone.utc)

    # 3 events for RELIANCE within the same 1-hour window
    events = [
        {
            "event_id": "EVT_001",
            "title": "Reliance announces major renewable energy expansion",
            "published_at_utc": (base_time + timedelta(minutes=5)).isoformat(),
            "detected_symbols": ["RELIANCE"],
        },
        {
            "event_id": "EVT_002",
            "title": "Reliance Q4 profit beats street estimates",
            "published_at_utc": (base_time + timedelta(minutes=15)).isoformat(),
            "detected_symbols": ["RELIANCE", "TCS"],
        },
        {
            "event_id": "EVT_003",
            "title": "Reliance Jio launches new enterprise cloud services",
            "published_at_utc": (base_time + timedelta(minutes=25)).isoformat(),
            "detected_symbols": ["RELIANCE"],
        },
        {
            "event_id": "EVT_004",
            "title": "HDFC Bank opens 100 new digital banking branches",
            "published_at_utc": (base_time + timedelta(minutes=20)).isoformat(),
            "detected_symbols": ["HDFCBANK"],
        },
    ]

    spikes = engine.process_micro_batch(events, current_time_utc=base_time + timedelta(minutes=30))

    # RELIANCE has 3 articles -> should trigger spike
    # TCS has 1 article -> no spike
    # HDFCBANK has 1 article -> no spike
    assert len(spikes) == 1
    spike = spikes[0]
    assert isinstance(spike, WindowSpikeResult)
    assert spike.symbol == "RELIANCE"
    assert spike.article_count == 3
    assert spike.threshold == 3
    assert spike.is_spike is True
    assert len(spike.sample_titles) == 3
    assert "SPIKE_RELIANCE_" in spike.spike_id


def test_micro_batch_drops_events_outside_watermark():
    engine = NewsSpikeStreamEngine(spike_threshold=2)
    latest_time = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)
    watermark_cutoff = latest_time - timedelta(minutes=10)  # 11:50:00

    # Both fresh events fall within the 11:00-12:00 window (11:50 and 11:55)
    events = [
        {
            "event_id": "EVT_LATE",
            "title": "Late arriving article on TCS",
            "published_at_utc": (latest_time - timedelta(minutes=30)).isoformat(),
            "detected_symbols": ["TCS"],
        },
        {
            "event_id": "EVT_FRESH_1",
            "title": "TCS fresh announcement 1",
            "published_at_utc": (latest_time - timedelta(minutes=10)).isoformat(),
            "detected_symbols": ["TCS"],
        },
        {
            "event_id": "EVT_FRESH_2",
            "title": "TCS fresh announcement 2",
            "published_at_utc": (latest_time - timedelta(minutes=5)).isoformat(),
            "detected_symbols": ["TCS"],
        },
    ]

    spikes = engine.process_micro_batch(
        events,
        watermark_cutoff_utc=watermark_cutoff,
        current_time_utc=latest_time,
    )

    # Only 2 fresh events remain after watermark drop; threshold is 2 -> spike detected with 2 count
    assert len(spikes) == 1
    assert spikes[0].symbol == "TCS"
    assert spikes[0].article_count == 2
    assert "Late arriving article on TCS" not in spikes[0].sample_titles


def test_micro_batch_handles_empty_or_malformed_events():
    engine = NewsSpikeStreamEngine(spike_threshold=2)
    assert engine.process_micro_batch([]) == []
    
    malformed = [
        {"event_id": "BAD_1", "title": "Missing fields"},
        {"event_id": "BAD_2", "published_at_utc": "invalid_date", "detected_symbols": ["INFY"]},
        {"event_id": "BAD_3", "published_at_utc": "2026-03-30T10:00:00Z", "detected_symbols": []},
    ]
    assert engine.process_micro_batch(malformed) == []
