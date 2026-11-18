"""Unit tests for Redpanda Docker Compose Manifest and Topic Provisioning Configuration."""
import os
import pytest
import yaml

from scripts.setup_streaming_topics import TOPIC_CONFIGS, provision_topics

COMPOSE_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "deployment", "docker", "docker-compose.streaming.yml"
)


def test_streaming_compose_manifest_structure():
    """Verify Docker Compose streaming profile configuration, memory limits, and ports."""
    assert os.path.exists(COMPOSE_FILE)

    with open(COMPOSE_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    services = config.get("services", {})
    assert "redpanda" in services
    assert "redpanda-console" in services

    # Verify Redpanda configuration & limits
    rp = services["redpanda"]
    assert "streaming" in rp.get("profiles", [])
    assert rp.get("mem_limit") == "1536m"  # 1.5 GB limit
    assert float(rp.get("cpus")) <= 1.5

    # Verify Redpanda Console configuration & limits
    rpc = services["redpanda-console"]
    assert "streaming" in rpc.get("profiles", [])
    assert rpc.get("mem_limit") == "256m"  # 256 MB limit


def test_topic_configs_specification():
    """Verify topic parameters adhere to architectural retention and partition rules."""
    topic_map = {t["name"]: t for t in TOPIC_CONFIGS}

    assert "news.events.raw" in topic_map
    assert "corporate.events.raw" in topic_map
    assert "news.intensity.spikes" in topic_map

    # news.events.raw: 3 partitions, 7 days retention
    news_topic = topic_map["news.events.raw"]
    assert news_topic["partitions"] == 3
    assert news_topic["config"]["retention.ms"] == str(7 * 24 * 60 * 60 * 1000)

    # corporate.events.raw: 3 partitions, 30 days retention
    corp_topic = topic_map["corporate.events.raw"]
    assert corp_topic["partitions"] == 3
    assert corp_topic["config"]["retention.ms"] == str(30 * 24 * 60 * 60 * 1000)


def test_provision_topics_dry_run():
    """Verify topic provisioning function runs cleanly in offline/dry-run mode."""
    # Test execution against unreachable mock port triggers dry-run validation without crashing
    results = provision_topics("localhost:9999")
    assert "news.events.raw" in results
    assert "corporate.events.raw" in results
    assert results["news.events.raw"] in ("SPEC_VALID", "CREATED", "EXISTS")
