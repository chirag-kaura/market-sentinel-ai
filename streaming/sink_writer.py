"""
Streaming Persistence Pipeline (Phase 4 — Step 4.6)
Market Sentinel AI — Streaming Sink Writer

Persists streaming events (news, corporate disclosures, spikes) to both:
1. Operational / Relational storage (PostgreSQL) with idempotent upsert.
2. Analytical partitioned Parquet storage for audit trails and feature engineering.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

import pandas as pd

logger = logging.getLogger("market_sentinel.streaming.sink_writer")
logger.setLevel(logging.INFO)


class StreamingSinkWriter:
    """
    Buffered sink writer for streaming event persistence.
    Accumulates records in memory and flushes them in batches to reduce I/O overhead.
    """

    def __init__(
        self,
        parquet_base_dir: str = "data/processed/streaming",
        buffer_size: int = 50,
        db_session_factory: Optional[Any] = None,
    ):
        self.parquet_base_dir = Path(parquet_base_dir)
        self.buffer_size = buffer_size
        self.db_session_factory = db_session_factory
        self._buffers: Dict[str, List[Dict[str, Any]]] = {
            "news": [],
            "corporate": [],
            "spikes": [],
        }

    def append_event(self, event_type: str, record: Dict[str, Any]) -> bool:
        """
        Appends an event to the appropriate type buffer.
        Automatically triggers flush if buffer reaches buffer_size.
        """
        if event_type not in self._buffers:
            self._buffers[event_type] = []

        self._buffers[event_type].append(record)

        if len(self._buffers[event_type]) >= self.buffer_size:
            self.flush(event_type=event_type)
            return True
        return False

    def flush(self, event_type: Optional[str] = None) -> Dict[str, int]:
        """
        Flushes buffered records to Parquet and relational storage.
        If event_type is None, flushes all active buffers.
        Returns a dictionary of written record counts per event type.
        """
        types_to_flush = [event_type] if event_type else list(self._buffers.keys())
        flush_counts: Dict[str, int] = {}

        for etype in types_to_flush:
            buffer = self._buffers.get(etype, [])
            if not buffer:
                flush_counts[etype] = 0
                continue

            # Copy and clear buffer immediately to avoid race conditions
            records_to_write = list(buffer)
            self._buffers[etype] = []

            # Write to Parquet analytical storage
            written_count = self._write_to_parquet(etype, records_to_write)
            flush_counts[etype] = written_count

            # Write to Relational database if session factory is provided
            if self.db_session_factory is not None:
                self._write_to_relational(etype, records_to_write)

        return flush_counts

    def _write_to_parquet(self, event_type: str, records: List[Dict[str, Any]]) -> int:
        """
        Writes batch of records to partitioned Snappy Parquet storage.
        """
        if not records:
            return 0

        df = pd.DataFrame(records)

        # Ensure timestamp column exists and parse for date partitioning
        time_col = None
        for candidate in ["published_at_utc", "filing_date_utc", "detected_at_utc"]:
            if candidate in df.columns:
                time_col = candidate
                break

        if time_col and not df.empty:
            # Parse timestamps
            parsed_dates = pd.to_datetime(df[time_col], utc=True, errors="coerce")
            # If all are NaT, fallback to current time
            if parsed_dates.isna().all():
                now = datetime.now(timezone.utc)
                year_str = str(now.year)
                month_str = f"{now.month:02d}"
                date_str = now.strftime("%Y-%m-%d")
            else:
                valid_date = parsed_dates.dropna().iloc[0]
                year_str = str(valid_date.year)
                month_str = f"{valid_date.month:02d}"
                date_str = valid_date.strftime("%Y-%m-%d")
        else:
            now = datetime.now(timezone.utc)
            year_str = str(now.year)
            month_str = f"{now.month:02d}"
            date_str = now.strftime("%Y-%m-%d")

        target_dir = self.parquet_base_dir / event_type / f"year={year_str}" / f"month={month_str}"
        target_dir.mkdir(parents=True, exist_ok=True)

        batch_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        file_path = target_dir / f"stream_{event_type}_{date_str}_{batch_timestamp}.parquet"

        # Convert complex objects (e.g. lists) to JSON strings or strings if writing to parquet
        df_to_save = df.copy()
        for col in df_to_save.columns:
            if df_to_save[col].apply(lambda x: isinstance(x, list)).any():
                df_to_save[col] = df_to_save[col].apply(
                    lambda x: ",".join(str(i) for i in x) if isinstance(x, list) else str(x)
                )

        # Deduplicate records by unique ID if present
        id_cols = [c for c in ["event_id", "spike_id", "canonical_url"] if c in df_to_save.columns]
        if id_cols:
            df_to_save = df_to_save.drop_duplicates(subset=[id_cols[0]])

        df_to_save.to_parquet(file_path, engine="pyarrow", compression="snappy", index=False)
        logger.info(f"Persisted {len(df_to_save)} {event_type} records to {file_path}")
        return len(df_to_save)

    @staticmethod
    def _parse_utc_datetime(value: Any) -> datetime:
        """Parse an ISO timestamp string or datetime into a UTC-aware datetime."""
        if isinstance(value, datetime):
            return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str) and value.strip():
            cleaned = value.strip()
            if cleaned.endswith("Z"):
                cleaned = cleaned[:-1] + "+00:00"
            try:
                parsed = datetime.fromisoformat(cleaned)
                return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return datetime.now(timezone.utc)

    def _write_to_relational(self, event_type: str, records: List[Dict[str, Any]]) -> None:
        """Persist buffered streaming records idempotently to the relational database."""
        if self.db_session_factory is None or not records:
            return

        if event_type == "spikes":
            logger.info("Skipping relational upsert for %d spike window records (archived in Parquet).", len(records))
            return

        from backend.models.market import (
            CorporateAnnouncementModel,
            NewsArticleModel,
            RiskAlertModel,
            SymbolMasterModel,
        )

        session = self.db_session_factory()
        inserted = 0
        try:
            valid_symbols = {row[0] for row in session.query(SymbolMasterModel.symbol).all()}

            if event_type == "news":
                seen_urls = set()
                for record in records:
                    url = str(record.get("canonical_url") or "").strip()[:1000]
                    title = str(record.get("title") or "").strip()[:500]
                    if not url or not title or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    existing = session.query(NewsArticleModel).filter_by(canonical_url=url).first()
                    if existing is None:
                        session.add(
                            NewsArticleModel(
                                id=str(record.get("event_id") or uuid.uuid4())[:36],
                                canonical_url=url,
                                title=title,
                                summary=record.get("summary"),
                                body_text=record.get("body_text"),
                                source_outlet=str(record.get("source_outlet") or "Unknown")[:100],
                                published_at_utc=self._parse_utc_datetime(record.get("published_at_utc")),
                                sentiment_score=0.0,
                                retrieval_timestamp_utc=self._parse_utc_datetime(record.get("ingested_at_utc")),
                                content_hash=record.get("headline_hash"),
                            )
                        )
                        inserted += 1

            elif event_type == "corporate":
                seen_keys = set()
                for record in records:
                    sym = str(record.get("symbol") or "").strip().upper()[:20]
                    subject = str(record.get("subject") or "").strip()[:500]
                    if not sym or sym not in valid_symbols or not subject:
                        continue
                    c_hash = hashlib.sha256(f"{sym}:{subject}".encode("utf-8")).hexdigest()
                    if (sym, c_hash) in seen_keys:
                        continue
                    seen_keys.add((sym, c_hash))
                    existing = (
                        session.query(CorporateAnnouncementModel)
                        .filter_by(symbol=sym, content_hash=c_hash)
                        .first()
                    )
                    if existing is None:
                        att_url = record.get("attachment_url")
                        session.add(
                            CorporateAnnouncementModel(
                                id=str(record.get("event_id") or uuid.uuid4())[:36],
                                symbol=sym,
                                category=str(record.get("category") or "CORPORATE_UPDATE")[:100],
                                subject=subject,
                                body_text=record.get("body_text"),
                                attachment_url=str(att_url)[:1000] if att_url else None,
                                published_at_utc=self._parse_utc_datetime(record.get("published_at_utc")),
                                source_provider=str(record.get("source_provider") or "SRC-REDPANDA-STREAM")[:50],
                                retrieval_timestamp_utc=self._parse_utc_datetime(record.get("ingested_at_utc")),
                                content_hash=c_hash,
                            )
                        )
                        inserted += 1

            elif event_type == "alerts":
                seen_ids = set()
                for record in records:
                    sym = str(record.get("symbol") or record.get("ticker") or "").strip().upper()[:20]
                    if not sym or sym not in valid_symbols:
                        continue
                    alert_id = str(
                        record.get("alert_id") or record.get("id") or record.get("event_id") or uuid.uuid4()
                    )[:36]
                    if alert_id in seen_ids:
                        continue
                    seen_ids.add(alert_id)
                    existing = session.query(RiskAlertModel).filter_by(id=alert_id).first()
                    if existing is None:
                        dt = self._parse_utc_datetime(
                            record.get("timestamp") or record.get("created_at_utc") or record.get("alert_date")
                        )
                        raw_score = (
                            record.get("composite_risk_score")
                            if record.get("composite_risk_score") is not None
                            else record.get("risk_score", 0.0)
                        )
                        session.add(
                            RiskAlertModel(
                                id=alert_id,
                                symbol=sym,
                                alert_date=dt.date(),
                                risk_score=float(raw_score),
                                priority_tier=str(record.get("priority_tier") or record.get("priority") or "MEDIUM")[:20],
                                alert_category=str(
                                    record.get("alert_category") or record.get("anomaly_type") or "SURVEILLANCE_ANOMALY"
                                )[:50],
                                summary_explanation=record.get("summary_explanation"),
                                abnormal_return=record.get("abnormal_return"),
                                volume_ratio=record.get("volume_ratio"),
                                sentiment_score=record.get("sentiment_score"),
                                novelty_score=record.get("novelty_score"),
                                has_matching_news=bool(record.get("has_matching_news", False)),
                                dossier_status=str(record.get("dossier_status") or "PENDING")[:30],
                                review_status=str(record.get("review_status") or "UNREVIEWED")[:30],
                                citations=list(record.get("citations") or []),
                                model_version=str(record.get("model_version") or "1.0.0")[:50],
                                created_at_utc=dt,
                            )
                        )
                        inserted += 1

            session.commit()
            logger.info("Relational sink persisted %d new %s records (batch=%d).", inserted, event_type, len(records))
        except Exception as err:
            session.rollback()
            logger.error("Relational write failed for %s: %s", event_type, err)
        finally:
            session.close()
