"""Financial News Event Producer for Redpanda.

Serializes and publishes verified financial news articles to Redpanda topic 'news.events.raw'.
Uses the primary detected symbol as the Kafka message key to ensure per-stock ordered partitions.
"""
from datetime import datetime, timezone
import json
import logging
import os
import uuid
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class NewsEventProducer:
    """Publishes validated NewsEventMessage payloads to Redpanda broker."""

    TOPIC_NAME = "news.events.raw"

    def __init__(self, bootstrap_servers: Optional[str] = None, mock_mode: bool = False):
        self.bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
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
                logger.warning("Could not connect to Kafka broker on %s: %s. Enabling mock mode.", self.bootstrap_servers, e)
                self.mock_mode = True

    def format_event_message(
        self,
        article_data: Dict,
        detected_symbols: Optional[List[str]] = None,
    ) -> Dict:
        """Construct a standardized NewsEventMessage dictionary matching JSON schema."""
        detected_symbols = detected_symbols or []
        event_id = str(uuid.uuid4())
        now_utc = datetime.now(timezone.utc).isoformat()

        pub_time = article_data.get("published_at_utc")
        if isinstance(pub_time, datetime):
            pub_time_str = pub_time.isoformat()
        else:
            pub_time_str = str(pub_time) if pub_time else now_utc

        headline_hash = article_data.get("headline_hash")
        if not headline_hash:
            import hashlib
            import re
            norm = re.sub(r"[^a-zA-Z0-9]", "", article_data.get("title", "").lower())
            headline_hash = hashlib.md5(norm.encode("utf-8")).hexdigest()

        return {
            "event_id": event_id,
            "canonical_url": article_data["canonical_url"],
            "title": article_data["title"],
            "summary": article_data.get("summary"),
            "body_text": article_data.get("body_text"),
            "source_outlet": article_data["source_outlet"],
            "detected_symbols": detected_symbols,
            "published_at_utc": pub_time_str,
            "ingested_at_utc": now_utc,
            "headline_hash": headline_hash,
        }

    def publish_news_event(
        self,
        article_data: Dict,
        detected_symbols: Optional[List[str]] = None,
    ) -> Dict:
        """Publish a single news event message to Redpanda."""
        message = self.format_event_message(article_data, detected_symbols)
        primary_symbol = detected_symbols[0] if detected_symbols else "MARKET"

        if self.mock_mode or not self.producer:
            self.published_messages.append({"key": primary_symbol, "value": message})
            logger.info("Mock-published news event %s for key %s", message["event_id"], primary_symbol)
            return message

        try:
            future = self.producer.send(self.TOPIC_NAME, key=primary_symbol, value=message)
            self.producer.flush()
            record_metadata = future.get(timeout=5)
            logger.info(
                "Published news event %s to partition %d at offset %d",
                message["event_id"],
                record_metadata.partition,
                record_metadata.offset,
            )
        except Exception as e:
            logger.error("Failed to publish news event %s: %s", message["event_id"], e)
            raise e

        return message

    def close(self):
        """Close producer connection."""
        if self.producer:
            self.producer.close()
