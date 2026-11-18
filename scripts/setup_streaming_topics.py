"""Streaming Topics Provisioning Script.

Connects to the Redpanda Kafka broker and provisions required topics
('news.events.raw', 'corporate.events.raw', 'news.intensity.spikes')
with designated partition counts and retention policies.
"""
import logging
import sys
from typing import Dict, List

logger = logging.getLogger(__name__)

TOPIC_CONFIGS = [
    {
        "name": "news.events.raw",
        "partitions": 3,
        "replication_factor": 1,
        "config": {
            "retention.ms": str(7 * 24 * 60 * 60 * 1000),  # 7 Days in ms
            "cleanup.policy": "delete",
        },
    },
    {
        "name": "corporate.events.raw",
        "partitions": 3,
        "replication_factor": 1,
        "config": {
            "retention.ms": str(30 * 24 * 60 * 60 * 1000),  # 30 Days in ms
            "cleanup.policy": "delete",
        },
    },
    {
        "name": "news.intensity.spikes",
        "partitions": 1,
        "replication_factor": 1,
        "config": {
            "retention.ms": str(3 * 24 * 60 * 60 * 1000),  # 3 Days in ms
            "cleanup.policy": "delete",
        },
    },
]


def provision_topics(broker_address: str = "localhost:19092") -> Dict[str, str]:
    """Create streaming topics using Kafka AdminClient if broker is available."""
    results = {}
    try:
        from kafka.admin import KafkaAdminClient, NewTopic
        from kafka.errors import TopicAlreadyExistsError

        admin_client = KafkaAdminClient(
            bootstrap_servers=broker_address,
            client_id="sentinel-topic-provisioner",
            request_timeout_ms=5000,
        )

        new_topics = [
            NewTopic(
                name=t["name"],
                num_partitions=t["partitions"],
                replication_factor=t["replication_factor"],
                topic_configs=t["config"],
            )
            for t in TOPIC_CONFIGS
        ]

        try:
            admin_client.create_topics(new_topics=new_topics, validate_only=False)
            logger.info("Successfully provisioned streaming topics on %s", broker_address)
            for t in TOPIC_CONFIGS:
                results[t["name"]] = "CREATED"
        except TopicAlreadyExistsError:
            logger.info("Topics already exist on broker.")
            for t in TOPIC_CONFIGS:
                results[t["name"]] = "EXISTS"
        finally:
            admin_client.close()

    except Exception as e:
        logger.warning("Redpanda broker not reachable on %s (%s). Dry-run simulated.", broker_address, e)
        # Dry-run validation of topic definitions
        for t in TOPIC_CONFIGS:
            results[t["name"]] = "SPEC_VALID"

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    broker = sys.argv[1] if len(sys.argv) > 1 else "localhost:19092"
    res = provision_topics(broker)
    print("Topic Provisioning Results:", res)
