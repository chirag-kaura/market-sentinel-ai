"""Resilient Corporate Disclosure Event Consumer.

Consumes CorporateEventMessage payloads from Redpanda topic 'corporate.events.raw'
under consumer group 'sentinel-corporate-consumers', validates against JSON schema,
enforces manual offset commits post-persistence, and routes poison-pill malformed
payloads to the dead-letter quarantine.
"""
from datetime import datetime, timezone
import json
import logging
import os
from typing import Dict, List, Optional
import jsonschema

logger = logging.getLogger(__name__)

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "schemas", "corporate_event_schema.json"
)


def _safe_json_deserialize(raw_bytes: Optional[bytes]) -> Dict:
    """Safely deserialize JSON payloads, wrapping malformed bytes so DLQ handles them."""
    if raw_bytes is None:
        return {"_malformed_raw": None}
    try:
        return json.loads(raw_bytes.decode("utf-8"))
    except Exception:
        return {"_malformed_raw": raw_bytes.decode("utf-8", errors="replace")}


class CorporateEventConsumer:
    """Consumer service for processing streaming corporate filings from Redpanda."""

    TOPIC_NAME = "corporate.events.raw"
    GROUP_ID = "sentinel-corporate-consumers"

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        dlq_file: str = "data/quarantine/invalid_stream_events.jsonl",
        mock_mode: bool = False,
    ):
        self.bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.dlq_file = dlq_file
        self.mock_mode = mock_mode
        self.consumer = None
        self.processed_events: List[Dict] = []
        os.makedirs(os.path.dirname(self.dlq_file), exist_ok=True)

        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

        if not self.mock_mode:
            try:
                from kafka import KafkaConsumer
                self.consumer = KafkaConsumer(
                    self.TOPIC_NAME,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=self.GROUP_ID,
                    enable_auto_commit=False,  # Manual commit post-persistence
                    auto_offset_reset="earliest",
                    value_deserializer=_safe_json_deserialize,
                    consumer_timeout_ms=5000,
                )
            except Exception as e:
                logger.warning("Could not connect to Kafka broker on %s: %s. Enabling mock mode.", self.bootstrap_servers, e)
                self.mock_mode = True

    def route_to_dlq(self, raw_payload: Dict, error_msg: str) -> None:
        """Route unparseable or schema-violating payload to dead-letter quarantine."""
        envelope = {
            "dlq_id": os.urandom(8).hex(),
            "topic": self.TOPIC_NAME,
            "error_message": error_msg,
            "raw_payload": raw_payload,
            "quarantined_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.dlq_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(envelope) + "\n")
        logger.warning("Routed invalid corporate message to streaming DLQ: %s", error_msg)

    def process_message(self, message_value: Dict) -> Optional[Dict]:
        """Validate payload against JSON schema and process event.

        Returns processed dictionary on success, or None if quarantined.
        """
        try:
            jsonschema.validate(instance=message_value, schema=self.schema)
        except jsonschema.ValidationError as e:
            self.route_to_dlq(message_value, f"Schema validation failed: {e.message}")
            return None

        # Record processed clean event
        self.processed_events.append(message_value)
        logger.info(
            "Successfully processed corporate event %s for symbol %s",
            message_value.get("event_id"),
            message_value.get("symbol"),
        )
        return message_value

    def consume_batch(
        self,
        max_messages: int = 50,
        timeout_ms: int = 1000,
        max_empty_polls: int = 4,
    ) -> List[Dict]:
        """Poll a bounded batch of messages from Redpanda, validate, and return clean records."""
        if self.mock_mode or not self.consumer:
            return []

        consumed: List[Dict] = []
        empty_polls = 0

        while len(consumed) < max_messages and empty_polls < max_empty_polls:
            remaining = max_messages - len(consumed)
            records_by_tp = self.consumer.poll(timeout_ms=timeout_ms, max_records=remaining)
            if not records_by_tp:
                empty_polls += 1
                continue

            empty_polls = 0
            for records in records_by_tp.values():
                for record in records:
                    processed = self.process_message(record.value)
                    if processed is not None:
                        consumed.append(processed)

        return consumed

    def commit_offsets(self):
        """Manually commit Kafka offsets following successful processing."""
        if self.consumer and not self.mock_mode:
            if self.consumer.assignment():
                self.consumer.commit()
                logger.info("Committed Kafka offsets for group %s", self.GROUP_ID)

    def close(self):
        """Close consumer connection."""
        if self.consumer:
            self.consumer.close()
