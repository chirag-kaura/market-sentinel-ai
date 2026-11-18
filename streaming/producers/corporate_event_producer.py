"""Corporate Disclosure Event Producer for Redpanda.

Serializes and publishes official corporate filings and regulatory announcements
to Redpanda topic 'corporate.events.raw'. Uses the exchange symbol as the message key
to ensure per-company sequential event ordering.
"""
from datetime import datetime, timezone
import json
import logging
import uuid
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CorporateEventProducer:
    """Publishes validated CorporateEventMessage payloads to Redpanda broker."""

    TOPIC_NAME = "corporate.events.raw"

    def __init__(self, bootstrap_servers: str = "localhost:19092", mock_mode: bool = False):
        self.bootstrap_servers = bootstrap_servers
        self.mock_mode = mock_mode
        self.producer = None
        self.published_messages: List[Dict] = []  # In-memory buffer for mock/testing mode

        if not self.mock_mode:
            try:
                from kafka import KafkaProducer
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    key_serializer=lambda k: k.encode("utf-8") if k else b"",
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    request_timeout_ms=5000,
                    retries=3,
                )
            except Exception as e:
                logger.warning("Could not connect to Kafka broker on %s: %s. Enabling mock mode.", bootstrap_servers, e)
                self.mock_mode = True

    def format_event_message(self, announcement_data: Dict) -> Dict:
        """Construct a standardized CorporateEventMessage dictionary matching JSON schema."""
        event_id = str(uuid.uuid4())
        now_utc = datetime.now(timezone.utc).isoformat()

        pub_time = announcement_data.get("published_at_utc")
        if isinstance(pub_time, datetime):
            pub_time_str = pub_time.isoformat()
        else:
            pub_time_str = str(pub_time) if pub_time else now_utc

        return {
            "event_id": event_id,
            "symbol": announcement_data["symbol"],
            "category": announcement_data.get("category", "GENERAL"),
            "subject": announcement_data["subject"],
            "body_text": announcement_data.get("body_text"),
            "attachment_url": announcement_data.get("attachment_url"),
            "published_at_utc": pub_time_str,
            "ingested_at_utc": now_utc,
            "source_provider": announcement_data.get("source_provider", "SRC-NSE-CORP-ANNOUNCEMENTS"),
        }

    def publish_corporate_event(self, announcement_data: Dict) -> Dict:
        """Publish a single corporate disclosure event message to Redpanda."""
        message = self.format_event_message(announcement_data)
        symbol_key = message["symbol"]

        if self.mock_mode or not self.producer:
            self.published_messages.append({"key": symbol_key, "value": message})
            logger.info("Mock-published corporate event %s for key %s", message["event_id"], symbol_key)
            return message

        try:
            future = self.producer.send(self.TOPIC_NAME, key=symbol_key, value=message)
            self.producer.flush()
            record_metadata = future.get(timeout=5)
            logger.info(
                "Published corporate event %s to partition %d at offset %d",
                message["event_id"],
                record_metadata.partition,
                record_metadata.offset,
            )
        except Exception as e:
            logger.error("Failed to publish corporate event %s: %s", message["event_id"], e)
            raise e

        return message

    def close(self):
        """Close producer connection."""
        if self.producer:
            self.producer.close()
