# Step Report: Phase 4 — Step 4.5: Spark Structured Streaming Processing

**Document ID**: `docs/step_reports/phase_04_step_05_spark_streaming.md`  
**Phase**: Phase 4 — Event Streaming and Distributed Processing  
**Step**: Step 4.5 — Spark Structured Streaming Processing (`news_spike_stream.py`)  
**Status**: APPROVED / COMPLETED  
**Date**: 2026-11-17  

---

## 1. Objective & Business Relevance
- **Objective**: Implement a distributed stream-processing pipeline using Spark Structured Streaming semantics (`processing/spark/news_spike_stream.py`) to consume news events from Redpanda (`news.events.raw`), parse unstructured event payloads, explode tagged company tickers, maintain event-time tumbling/sliding windows with watermarks, compute symbol-level news arrival velocity, and detect statistically significant news intensity spikes in real-time.
- **Business Relevance**: When abnormal stock price or volume movements occur, regulatory surveillance officers must immediately determine whether the volatility is backed by verified public corporate disclosures or if suspicious trading activity took place prior to material news. Computing real-time news intensity windows provides the temporal foundation for cross-modal correlation alerts (Phase 8).

---

## 2. Technical Explanation & Architectural Fit
- **Windowing & Watermarking**:
  - Event-time watermark: 10 minutes (`withWatermark("published_at_utc", "10 minutes")`).
  - Window duration: 1 hour tumbling/sliding window.
  - Spike condition: $\ge 3$ news events per symbol within the window (configurable threshold).
  - Output Topic: `news.intensity.spikes`.
- **Dual-Engine Architecture (Hardware-Conscious Development)**:
  - **Native PySpark Streaming Query**: Pre-configured with PySpark SQL functions (`readStream.format("kafka")`, `from_json`, `withWatermark`, `groupBy(window, symbol).count()`, `writeStream`) designed for containerized execution inside the Docker `data` / `streaming` profile.
  - **Micro-Batch / Simulation Engine**: Implemented using Pandas vector operations, allowing complete deterministic unit testing and CI execution on Windows 11 host environments without requiring a local multi-gigabyte Java Virtual Machine (JVM).

---

## 3. Technology Decisions & Alternatives Considered
- **PySpark Structured Streaming vs. Flink**:
  - Selected PySpark Structured Streaming due to seamless interoperability with Python-based data pipelines (Airflow, Scikit-learn, Pandas) and existing team proficiency.
- **Micro-Batch Simulation in Dev**:
  - Preserves system RAM (< 16 GB constraint) by avoiding local Spark JVM daemon initialization during rapid unit testing cycles.

---

## 4. Files Created / Modified
- `processing/spark/news_spike_stream.py`: Full Spark Structured Streaming query definition and micro-batch simulation engine.
- `tests/unit/test_spark_streaming.py`: Comprehensive test suite verifying initialization, threshold triggering, watermark cutoffs, and malformed payload filtering.
- `docs/step_reports/phase_04_step_05_spark_streaming.md`: Step documentation and operational guidelines.
- `docs/PROJECT_TRACKER.md`: Updated Step 4.5 status to `COMPLETED`.
- `docs/CHANGELOG.md`: Logged Step 4.5 completion.

---

## 5. Commands Executed & Testing Report
- **Command**: `python -m pytest tests/unit/test_spark_streaming.py -v`
  - Output: `4 passed in 2.82s`
- **Command**: `python -m pytest tests/ -v`
  - Output: `31 passed in 8.60s` across all 31 repository test cases.

---

## 6. Known Limitations, Risks & Edge Cases
- **JVM Dependency**: PySpark native execution requires Java 8/11/17 when running outside Docker. The containerized deployment profile handles this automatically.
- **Watermark Tuning**: If news feeds experience severe distribution delay (> 10 minutes latency), late-arriving events will be dropped from the real-time intensity window. Batch deduplication (Step 3.4) guarantees eventual consistency in analytical storage.

---

## 7. Status & Next Step
- **Step 4.5 Status**: COMPLETED & VERIFIED.
- **Proposed Next Step**: Proceed to **Phase 4 — Step 4.6: Streaming Persistence Pipeline** (`streaming/sink_writer.py` to persist streaming event records to PostgreSQL and Parquet).
