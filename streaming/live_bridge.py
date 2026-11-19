"""Live Redpanda Streaming Bridge for Market Sentinel AI.

Connects PostgreSQL 16 surveillance tables, Python Producers/Consumers, Parquet
analytical storage, Prometheus metrics, and FastAPI Server-Sent Events (SSE)
through the local Redpanda broker (default: ``localhost:9092``).
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
import logging
import os
import re
import socket
import uuid
from typing import Any, Dict, List, Optional, Tuple

from backend.core.metrics import SURVEILLANCE_ALERTS_TOTAL
from streaming.consumers.corporate_event_consumer import CorporateEventConsumer
from streaming.consumers.news_event_consumer import NewsEventConsumer
from streaming.producers.corporate_event_producer import CorporateEventProducer
from streaming.producers.news_event_producer import NewsEventProducer
from streaming.sink_writer import StreamingSinkWriter

logger = logging.getLogger("market_sentinel.streaming.live_bridge")

QUOTES_TOPIC = "market.quotes.raw"
ALERTS_TOPIC = "surveillance.alerts.live"
ALERT_SSE_GROUP_ID = "sentinel-alert-sse-bridge"

SYMBOL_KEYWORDS: Dict[str, List[str]] = {
    "RELIANCE": ["reliance", "ril"],
    "INFY": ["infosys", "infy"],
    "TCS": ["tcs", "tata consultancy"],
    "HDFCBANK": ["hdfcbank", "hdfc bank", "hdfc"],
    "ICICIBANK": ["icicibank", "icici bank", "icici"],
    "MARUTI": ["maruti", "maruti suzuki"],
    "LT": ["larsen", "l&t"],
    "SBIN": ["sbin", "sbi", "state bank of india", "state bank"],
    "ITC": ["itc"],
    "BHARTIARTL": ["bhartiartl", "bharti airtel", "airtel"],
    "HINDUNILVR": ["hindunilvr", "hindustan unilever", "hul"],
    "KOTAKBANK": ["kotakbank", "kotak mahindra", "kotak bank", "kotak"],
    "AXISBANK": ["axisbank", "axis bank"],
    "SUNPHARMA": ["sunpharma", "sun pharma", "sun pharmaceutical"],
    "BAJFINANCE": ["bajfinance", "bajaj finance"],
}


def get_bootstrap_servers(override: Optional[str] = None) -> str:
    """Resolve Redpanda/Kafka bootstrap servers from override or environment."""
    return override or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


def _safe_json_deserialize(raw_bytes: Optional[bytes]) -> Dict[str, Any]:
    """Decode JSON bytes safely without crashing Kafka poll loops."""
    if raw_bytes is None:
        return {"_malformed_raw": None}
    try:
        parsed = json.loads(raw_bytes.decode("utf-8"))
        if isinstance(parsed, dict):
            return parsed
        return {"_malformed_raw": str(parsed)}
    except Exception:
        return {"_malformed_raw": raw_bytes.decode("utf-8", errors="replace")}


def _parse_host_port(bootstrap_servers: str) -> Tuple[str, int]:
    """Extract primary host and TCP port from a Kafka bootstrap string."""
    first = bootstrap_servers.split(",")[0].strip()
    if ":" in first:
        host, _, port_str = first.rpartition(":")
        try:
            return host or "localhost", int(port_str)
        except ValueError:
            pass
    return first or "localhost", 9092


def _is_broker_reachable(bootstrap_servers: str, timeout: float = 1.0) -> bool:
    """Check fast TCP reachability to the Redpanda broker."""
    host, port = _parse_host_port(bootstrap_servers)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def detect_symbols_in_text(text: str, known_symbols: List[str]) -> List[str]:
    """Match Top-15 NSE symbols and canonical company keywords in headline/summary text."""
    if not text:
        return []

    lowered = text.lower()
    matched: List[str] = []

    for sym in known_symbols:
        sym_upper = sym.upper()
        # Exact ticker boundary match (strict uppercase for short 2-letter LT to avoid false positives)
        if sym_upper == "LT":
            if re.search(r"\bLT\b", text):
                matched.append(sym_upper)
                continue
        elif re.search(rf"\b{re.escape(sym.lower())}\b", lowered):
            matched.append(sym_upper)
            continue

        keywords = SYMBOL_KEYWORDS.get(sym_upper, [])
        for kw in keywords:
            if "&" in kw:
                if kw in lowered:
                    matched.append(sym_upper)
                    break
            elif re.search(rf"\b{re.escape(kw)}\b", lowered):
                matched.append(sym_upper)
                break

    return matched


def normalize_alert_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw Redpanda or DB alert dicts into canonical SSE alert schema."""
    ticker = str(payload.get("ticker") or payload.get("symbol") or "MARKET").strip().upper() or "MARKET"
    event_id = str(payload.get("event_id") or payload.get("alert_id") or payload.get("id") or uuid.uuid4())
    priority = str(payload.get("priority") or payload.get("priority_tier") or "MEDIUM").strip().upper() or "MEDIUM"
    anomaly_type = str(
        payload.get("anomaly_type")
        or payload.get("alert_category")
        or payload.get("category")
        or "SURVEILLANCE_ANOMALY"
    ).strip()

    raw_score = (
        payload.get("composite_risk_score")
        if payload.get("composite_risk_score") is not None
        else payload.get("risk_score", 0.0)
    )
    try:
        composite_risk_score = float(raw_score) if raw_score is not None else 0.0
    except (TypeError, ValueError):
        composite_risk_score = 0.0

    ts_raw = (
        payload.get("timestamp")
        or payload.get("created_at_utc")
        or payload.get("alert_date")
        or datetime.now(timezone.utc).isoformat()
    )
    timestamp = ts_raw.isoformat() if hasattr(ts_raw, "isoformat") else str(ts_raw)

    summary_explanation = str(
        payload.get("summary_explanation")
        or payload.get("summary")
        or f"Live surveillance alert for {ticker} ({priority})"
    )

    return {
        "event_id": event_id,
        "timestamp": timestamp,
        "ticker": ticker,
        "anomaly_type": anomaly_type,
        "composite_risk_score": composite_risk_score,
        "priority": priority,
        "summary_explanation": summary_explanation,
        "feed_source": "REDPANDA_LIVE",
    }


def publish_alert_events(alerts: List[Dict[str, Any]], bootstrap_servers: Optional[str] = None) -> int:
    """Publish authentic surveillance alert records to Redpanda 'surveillance.alerts.live'."""
    if not alerts:
        return 0

    broker = get_bootstrap_servers(bootstrap_servers)
    producer = None
    sent = 0
    try:
        from kafka import KafkaProducer

        producer = KafkaProducer(
            bootstrap_servers=broker,
            key_serializer=lambda k: k.encode("utf-8") if k else b"",
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            request_timeout_ms=5000,
            retries=2,
        )
        for raw_alert in alerts:
            normalized = normalize_alert_payload(raw_alert)
            producer.send(ALERTS_TOPIC, key=normalized["ticker"], value=normalized)
            sent += 1
        producer.flush(timeout=5)
        logger.info("Published %d alerts to %s (%s).", sent, ALERTS_TOPIC, broker)
        return sent
    except Exception as exc:
        logger.warning("Could not publish alert events to Redpanda (%s): %s", broker, exc)
        return 0
    finally:
        if producer is not None:
            producer.close()


def publish_quote_events(quotes: List[Dict[str, Any]], bootstrap_servers: Optional[str] = None) -> int:
    """Publish authentic OHLCV quote snapshots to Redpanda 'market.quotes.raw'."""
    if not quotes:
        return 0

    broker = get_bootstrap_servers(bootstrap_servers)
    producer = None
    sent = 0
    try:
        from kafka import KafkaProducer

        producer = KafkaProducer(
            bootstrap_servers=broker,
            key_serializer=lambda k: k.encode("utf-8") if k else b"",
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            request_timeout_ms=5000,
            retries=2,
        )
        for quote in quotes:
            sym = str(quote.get("symbol") or "MARKET").strip().upper()
            producer.send(QUOTES_TOPIC, key=sym, value=quote)
            sent += 1
        producer.flush(timeout=5)
        logger.info("Published %d quote snapshots to %s (%s).", sent, QUOTES_TOPIC, broker)
        return sent
    except Exception as exc:
        logger.warning("Could not publish quote events to Redpanda (%s): %s", broker, exc)
        return 0
    finally:
        if producer is not None:
            producer.close()


def publish_real_events_from_db(
    bootstrap_servers: Optional[str] = None,
    limit_per_topic: int = 15,
) -> Dict[str, int]:
    """Read authentic records from PostgreSQL 16 and stream them across all 4 Redpanda topics."""
    from backend.core.database import SessionLocal
    from backend.models.market import (
        CorporateAnnouncementModel,
        MarketQuoteModel,
        NewsArticleModel,
        RiskAlertModel,
        SymbolMasterModel,
    )

    broker = get_bootstrap_servers(bootstrap_servers)
    counts: Dict[str, int] = {
        QUOTES_TOPIC: 0,
        NewsEventProducer.TOPIC_NAME: 0,
        CorporateEventProducer.TOPIC_NAME: 0,
        ALERTS_TOPIC: 0,
    }

    session = SessionLocal()
    news_producer: Optional[NewsEventProducer] = None
    corp_producer: Optional[CorporateEventProducer] = None

    try:
        known_symbols = [
            row[0]
            for row in session.query(SymbolMasterModel.symbol)
            .filter_by(is_active=True)
            .order_by(SymbolMasterModel.symbol)
            .all()
        ]

        # 1. Latest authentic OHLCV quote per VIP symbol -> market.quotes.raw
        quote_payloads: List[Dict[str, Any]] = []
        for sym in known_symbols[:limit_per_topic]:
            latest_q = (
                session.query(MarketQuoteModel)
                .filter_by(symbol=sym)
                .order_by(MarketQuoteModel.trade_date.desc())
                .first()
            )
            if latest_q is not None:
                quote_payloads.append(
                    {
                        "event_id": str(latest_q.id),
                        "symbol": latest_q.symbol,
                        "trade_date": latest_q.trade_date.isoformat(),
                        "open_price": float(latest_q.open_price),
                        "high_price": float(latest_q.high_price),
                        "low_price": float(latest_q.low_price),
                        "close_price": float(latest_q.close_price),
                        "volume": int(latest_q.volume),
                        "turnover": float(latest_q.turnover),
                        "source_provider": latest_q.source_provider,
                        "published_at_utc": datetime.now(timezone.utc).isoformat(),
                    }
                )
        counts[QUOTES_TOPIC] = publish_quote_events(quote_payloads, bootstrap_servers=broker)

        # 2. Recent authentic news articles -> news.events.raw
        news_rows = (
            session.query(NewsArticleModel)
            .order_by(NewsArticleModel.published_at_utc.desc())
            .limit(limit_per_topic * 2)
            .all()
        )
        news_producer = NewsEventProducer(bootstrap_servers=broker)
        if not news_producer.mock_mode:
            sent_news = 0
            for art in news_rows:
                if sent_news >= limit_per_topic:
                    break
                title = (art.title or "").strip()
                if len(title) < 10 or not art.canonical_url:
                    continue
                detected = detect_symbols_in_text(f"{title} {art.summary or ''}", known_symbols)
                news_producer.publish_news_event(
                    {
                        "canonical_url": art.canonical_url,
                        "title": title[:500],
                        "summary": art.summary,
                        "body_text": art.body_text,
                        "source_outlet": art.source_outlet,
                        "published_at_utc": art.published_at_utc,
                        "headline_hash": art.content_hash,
                    },
                    detected_symbols=detected,
                )
                sent_news += 1
            counts[NewsEventProducer.TOPIC_NAME] = sent_news

        # 3. Recent authentic corporate announcements -> corporate.events.raw
        corp_rows = (
            session.query(CorporateAnnouncementModel)
            .order_by(CorporateAnnouncementModel.published_at_utc.desc())
            .limit(limit_per_topic * 2)
            .all()
        )
        corp_producer = CorporateEventProducer(bootstrap_servers=broker)
        if not corp_producer.mock_mode:
            sent_corp = 0
            for ann in corp_rows:
                if sent_corp >= limit_per_topic:
                    break
                subject = (ann.subject or "").strip()
                if len(subject) < 5 or not ann.symbol:
                    continue
                corp_producer.publish_corporate_event(
                    {
                        "symbol": ann.symbol,
                        "category": ann.category,
                        "subject": subject[:500],
                        "body_text": ann.body_text,
                        "attachment_url": ann.attachment_url or None,
                        "published_at_utc": ann.published_at_utc,
                        "source_provider": ann.source_provider,
                    }
                )
                sent_corp += 1
            counts[CorporateEventProducer.TOPIC_NAME] = sent_corp

        # 4. Recent authentic surveillance risk alerts -> surveillance.alerts.live
        alert_rows = (
            session.query(RiskAlertModel)
            .order_by(RiskAlertModel.alert_date.desc(), RiskAlertModel.risk_score.desc())
            .limit(limit_per_topic)
            .all()
        )
        alert_payloads = [
            {
                "id": al.id,
                "symbol": al.symbol,
                "alert_date": al.alert_date.isoformat(),
                "created_at_utc": al.created_at_utc.isoformat() if al.created_at_utc else al.alert_date.isoformat(),
                "risk_score": float(al.risk_score),
                "priority_tier": al.priority_tier,
                "alert_category": al.alert_category,
                "summary_explanation": al.summary_explanation,
            }
            for al in alert_rows
        ]
        counts[ALERTS_TOPIC] = publish_alert_events(alert_payloads, bootstrap_servers=broker)
        return counts
    finally:
        if news_producer is not None:
            news_producer.close()
        if corp_producer is not None:
            corp_producer.close()
        session.close()


def consume_and_persist_batch(
    bootstrap_servers: Optional[str] = None,
    max_messages_per_topic: int = 50,
) -> Dict[str, int]:
    """Consume live news & corporate batches from Redpanda, write Parquet + Postgres, commit offsets."""
    from backend.core.database import SessionLocal

    broker = get_bootstrap_servers(bootstrap_servers)
    news_consumer = NewsEventConsumer(bootstrap_servers=broker)
    corp_consumer = CorporateEventConsumer(bootstrap_servers=broker)
    sink_writer = StreamingSinkWriter(
        parquet_base_dir="data/processed/streaming",
        buffer_size=50,
        db_session_factory=SessionLocal,
    )

    try:
        news_batch = news_consumer.consume_batch(max_messages=max_messages_per_topic)
        for item in news_batch:
            sink_writer.append_event("news", item)

        corp_batch = corp_consumer.consume_batch(max_messages=max_messages_per_topic)
        for item in corp_batch:
            sink_writer.append_event("corporate", item)

        flush_counts = sink_writer.flush()

        if not news_consumer.mock_mode and news_batch:
            news_consumer.commit_offsets()
        if not corp_consumer.mock_mode and corp_batch:
            corp_consumer.commit_offsets()

        return {
            "news_consumed": len(news_batch),
            "corporate_consumed": len(corp_batch),
            "news_parquet_written": flush_counts.get("news", 0),
            "corporate_parquet_written": flush_counts.get("corporate", 0),
        }
    finally:
        news_consumer.close()
        corp_consumer.close()


async def poll_live_alerts_to_sse_loop(
    bootstrap_servers: Optional[str] = None,
    poll_interval_seconds: float = 1.0,
) -> None:
    """Continuously bridge 'surveillance.alerts.live' -> Prometheus + FastAPI SSE broker."""
    from backend.api.v1.endpoints.stream import AlertStreamBroker

    broker = get_bootstrap_servers(bootstrap_servers)

    while True:
        consumer = None
        try:
            reachable = await asyncio.to_thread(_is_broker_reachable, broker, 1.0)
            if not reachable:
                logger.info("Redpanda broker not reachable on %s; alert SSE bridge sleeping 30s.", broker)
                await asyncio.sleep(30.0)
                continue

            from kafka import KafkaConsumer

            consumer = await asyncio.to_thread(
                KafkaConsumer,
                ALERTS_TOPIC,
                bootstrap_servers=broker,
                group_id=ALERT_SSE_GROUP_ID,
                enable_auto_commit=False,
                auto_offset_reset="earliest",
                value_deserializer=_safe_json_deserialize,
            )
            logger.info("Connected FastAPI SSE bridge to Redpanda topic '%s' (%s).", ALERTS_TOPIC, broker)

            while True:
                records_by_tp = await asyncio.to_thread(consumer.poll, 500, 25)
                processed_any = False

                if records_by_tp:
                    for records in records_by_tp.values():
                        for record in records:
                            raw_val = record.value
                            if not isinstance(raw_val, dict) or "_malformed_raw" in raw_val:
                                logger.warning("Skipped malformed payload on %s offset %s.", ALERTS_TOPIC, record.offset)
                                processed_any = True
                                continue

                            evt = normalize_alert_payload(raw_val)
                            SURVEILLANCE_ALERTS_TOTAL.labels(
                                ticker=evt["ticker"],
                                priority=evt["priority"],
                                anomaly_category=evt["anomaly_type"],
                            ).inc()
                            await AlertStreamBroker.publish_alert(evt)
                            processed_any = True

                if processed_any and consumer.assignment():
                    await asyncio.to_thread(consumer.commit)

                await asyncio.sleep(poll_interval_seconds)

        except asyncio.CancelledError:
            logger.info("Stopping Redpanda alert SSE consumer loop cleanly.")
            break
        except Exception as exc:
            logger.warning("Redpanda alert SSE bridge interrupted (%s); retrying in 5s.", exc)
            await asyncio.sleep(5.0)
        finally:
            if consumer is not None:
                try:
                    await asyncio.to_thread(consumer.close)
                except Exception:
                    pass


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Market Sentinel AI — Live Redpanda Producer/Consumer Bridge")
    parser.add_argument("--publish-only", action="store_true", help="Only publish recent DB events to Redpanda.")
    parser.add_argument("--consume-only", action="store_true", help="Only consume queued Redpanda events to sinks.")
    parser.add_argument("--limit", type=int, default=15, help="Max records per topic when publishing (default: 15).")
    args = parser.parse_args()

    summary: Dict[str, Any] = {}
    if not args.consume_only:
        summary["published"] = publish_real_events_from_db(limit_per_topic=args.limit)
    if not args.publish_only:
        summary["consumed"] = consume_and_persist_batch(max_messages_per_topic=max(args.limit * 2, 50))

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
