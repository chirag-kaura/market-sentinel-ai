"""
News Spike Stream Processor (Phase 4 — Step 4.5)
Market Sentinel AI — Stream Processing Layer

Computes real-time news arrival velocity per symbol over event-time tumbling or
sliding windows using Spark Structured Streaming semantics. Flags sudden clusters
of corporate news or sentiment shifts (news intensity spikes) for downstream
investigative correlation.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger("market_sentinel.processing.spark_streaming")
logger.setLevel(logging.INFO)


NEWS_SPIKE_SCHEMA_FIELDS = {
    "spike_id": str,
    "symbol": str,
    "window_start": str,
    "window_end": str,
    "article_count": int,
    "threshold": int,
    "is_spike": bool,
    "sample_titles": list,
    "detected_at_utc": str,
}


@dataclass
class WindowSpikeResult:
    spike_id: str
    symbol: str
    window_start: str
    window_end: str
    article_count: int
    threshold: int
    is_spike: bool
    sample_titles: List[str]
    detected_at_utc: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spike_id": self.spike_id,
            "symbol": self.symbol,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "article_count": self.article_count,
            "threshold": self.threshold,
            "is_spike": self.is_spike,
            "sample_titles": self.sample_titles,
            "detected_at_utc": self.detected_at_utc,
        }


class NewsSpikeStreamEngine:
    """
    Stream analytics engine implementing event-time windowing and spike detection.
    
    Provides dual operation:
    1. Native PySpark Structured Streaming pipeline definition for container execution.
    2. Micro-batch / simulation engine for test validation on CPU-only/JVM-less hosts.
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        input_topic: str = "news.events.raw",
        output_topic: str = "news.intensity.spikes",
        window_duration: str = "1 hour",
        slide_duration: str = "15 minutes",
        watermark_delay: str = "10 minutes",
        spike_threshold: int = 3,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.window_duration = window_duration
        self.slide_duration = slide_duration
        self.watermark_delay = watermark_delay
        self.spike_threshold = spike_threshold

    def build_pyspark_streaming_query(self, spark_session: Any) -> Any:
        """
        Builds the PySpark Structured Streaming query when PySpark is available.
        """
        try:
            from pyspark.sql import functions as F
            from pyspark.sql.types import (
                ArrayType,
                StringType,
                StructField,
                StructType,
                TimestampType,
            )
        except ImportError as err:
            raise RuntimeError(
                "PySpark is not installed in the local environment. "
                "Use the micro-batch simulation engine or run inside the Spark Docker profile."
            ) from err

        news_event_schema = StructType([
            StructField("event_id", StringType(), False),
            StructField("canonical_url", StringType(), False),
            StructField("title", StringType(), False),
            StructField("publisher", StringType(), False),
            StructField("published_at_utc", TimestampType(), False),
            StructField("detected_symbols", ArrayType(StringType()), True),
            StructField("language", StringType(), True),
            StructField("summary", StringType(), True),
        ])

        # Read from Redpanda / Kafka
        raw_stream = (
            spark_session.readStream.format("kafka")
            .option("kafka.bootstrap.servers", self.bootstrap_servers)
            .option("subscribe", self.input_topic)
            .option("startingOffsets", "latest")
            .load()
        )

        parsed_stream = (
            raw_stream.selectExpr("CAST(value AS STRING) as json_payload")
            .select(F.from_json(F.col("json_payload"), news_event_schema).alias("data"))
            .select("data.*")
        )

        exploded_stream = parsed_stream.withColumn(
            "symbol", F.explode_outer("detected_symbols")
        ).filter(F.col("symbol").isNotNull())

        watermarked_stream = exploded_stream.withWatermark(
            "published_at_utc", self.watermark_delay
        )

        aggregated_stream = (
            watermarked_stream.groupBy(
                F.window("published_at_utc", self.window_duration, self.slide_duration),
                F.col("symbol"),
            )
            .agg(
                F.count("event_id").alias("article_count"),
                F.collect_list("title").alias("sample_titles"),
            )
            .filter(F.col("article_count") >= self.spike_threshold)
            .select(
                F.concat_ws("_", F.col("symbol"), F.col("window.start")).alias("spike_id"),
                F.col("symbol"),
                F.col("window.start").cast(StringType()).alias("window_start"),
                F.col("window.end").cast(StringType()).alias("window_end"),
                F.col("article_count"),
                F.lit(self.spike_threshold).alias("threshold"),
                F.lit(True).alias("is_spike"),
                F.col("sample_titles"),
                F.current_timestamp().cast(StringType()).alias("detected_at_utc"),
            )
        )

        # Output to Redpanda / Kafka topic
        sink_query = (
            aggregated_stream.selectExpr(
                "CAST(spike_id AS STRING) AS key",
                "to_json(struct(*)) AS value",
            )
            .writeStream.format("kafka")
            .option("kafka.bootstrap.servers", self.bootstrap_servers)
            .option("topic", self.output_topic)
            .option("checkpointLocation", "/tmp/spark_checkpoints/news_spike_stream")
            .outputMode("update")
            .start()
        )

        return sink_query

    def process_micro_batch(
        self,
        events: List[Dict[str, Any]],
        watermark_cutoff_utc: Optional[datetime] = None,
        current_time_utc: Optional[datetime] = None,
    ) -> List[WindowSpikeResult]:
        """
        Micro-batch stream simulator evaluating event windows, watermark dropoffs,
        and threshold spike alerts. Enables unit testing and offline execution.
        """
        if not events:
            return []

        now = current_time_utc or datetime.now(timezone.utc)
        flat_records = []

        for ev in events:
            # Parse published_at
            pub_raw = ev.get("published_at_utc")
            if isinstance(pub_raw, str):
                try:
                    pub_time = datetime.fromisoformat(pub_raw.replace("Z", "+00:00"))
                except ValueError:
                    continue
            elif isinstance(pub_raw, datetime):
                pub_time = pub_raw
            else:
                continue

            # Ensure UTC timezone
            if pub_time.tzinfo is None:
                pub_time = pub_time.replace(tzinfo=timezone.utc)
            else:
                pub_time = pub_time.astimezone(timezone.utc)

            symbols = ev.get("detected_symbols") or []
            if not symbols:
                continue

            for sym in symbols:
                flat_records.append({
                    "event_id": ev.get("event_id"),
                    "title": ev.get("title", ""),
                    "symbol": sym.strip().upper(),
                    "published_at": pub_time,
                })

        if not flat_records:
            return []

        df = pd.DataFrame(flat_records)

        # In Spark Structured Streaming, late records arriving after watermark are dropped.
        # If watermark_cutoff_utc is provided, filter out events before it.
        if watermark_cutoff_utc is not None:
            cutoff = watermark_cutoff_utc
            if cutoff.tzinfo is None:
                cutoff = cutoff.replace(tzinfo=timezone.utc)
            else:
                cutoff = cutoff.astimezone(timezone.utc)
            df_valid = df[df["published_at"] >= cutoff].copy()
        else:
            df_valid = df.copy()

        if df_valid.empty:
            return []

        # Floor into 1-hour tumbling window bucket
        df_valid["window_start"] = df_valid["published_at"].dt.floor("1h")
        df_valid["window_end"] = df_valid["window_start"] + pd.Timedelta(hours=1)

        grouped = (
            df_valid.groupby(["symbol", "window_start", "window_end"])
            .agg(
                article_count=("event_id", "count"),
                sample_titles=("title", list),
            )
            .reset_index()
        )

        spikes: List[WindowSpikeResult] = []
        for _, row in grouped.iterrows():
            count = int(row["article_count"])
            if count >= self.spike_threshold:
                w_start_str = row["window_start"].isoformat()
                w_end_str = row["window_end"].isoformat()
                spike_id = f"SPIKE_{row['symbol']}_{int(row['window_start'].timestamp())}"

                spikes.append(
                    WindowSpikeResult(
                        spike_id=spike_id,
                        symbol=row["symbol"],
                        window_start=w_start_str,
                        window_end=w_end_str,
                        article_count=count,
                        threshold=self.spike_threshold,
                        is_spike=True,
                        sample_titles=list(row["sample_titles"]),
                        detected_at_utc=now.isoformat(),
                    )
                )

        return spikes
