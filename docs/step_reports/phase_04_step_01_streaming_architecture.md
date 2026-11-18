# STEP IMPLEMENTATION REPORT
## Phase 4 — Step 4.1: Streaming Architecture & Event Schemas
**Project**: Market Sentinel AI  
**Date**: 2026-11-17  
**Status**: COMPLETED (Awaiting User Sign-Off)

---

### 1. Objective & Business Relevance
- **Objective**: Formulate the event streaming architecture, topic topology, message key partitioning strategies, consumer offset management, and formal Draft-07 JSON schemas for incoming news and corporate announcements, strictly respecting the 16 GB RAM host environment via Docker Compose profile containment (`streaming`).
- **Business Relevance**: Establishes the real-time event ingestion infrastructure for financial news and regulatory filings, allowing newly published corporate events to be processed, deduplicated, and correlated with market anomalies in near real-time without violating data authenticity or host memory boundaries.

### 2. Technical Explanation & Architectural Fit
- Authored [`docs/architecture/streaming_architecture.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/architecture/streaming_architecture.md):
  - **Legitimate Stream Scope**: Streams are strictly dedicated to genuine news and corporate filings. Static historical CSV files are explicitly banned from streaming brokers.
  - **Hardware Containment**: Encapsulated under the `streaming` Docker Compose profile. Redpanda is capped at $1.5\text{ GB}$ RAM; single-node Spark is capped at $2.0\text{ GB}$ RAM ($\le 3.5\text{ GB}$ total).
  - **Topic Topology**:
    - `news.events.raw`: 3 partitions, keyed by primary detected symbol or `'MARKET'`, 7-day retention.
    - `corporate.events.raw`: 3 partitions, keyed by primary exchange symbol, 30-day retention.
    - `news.intensity.spikes`: 1 partition, derived stream for statistical volume spikes.
  - **Message Key Partitioning**: Partitioning by symbol guarantees strict monotonic event ordering per company, eliminating race conditions during RAG dossier synthesis.
  - **Consumer Group & DLQ**: Manual offset commit post-database persistence; poison-pill payloads route to `streaming.dead_letter.events`.
- Formulated Draft-07 JSON schemas:
  - [`streaming/schemas/news_event_schema.json`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/streaming/schemas/news_event_schema.json): Schematized headline, canonical URL, source outlet, publication/ingestion timestamps, detected symbols, and MD5 headline hash.
  - [`streaming/schemas/corporate_event_schema.json`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/streaming/schemas/corporate_event_schema.json): Schematized symbol, event category, subject, filing body text, PDF URL, and source provider.
- Authored automated unit test suite `tests/unit/test_streaming_schemas.py` using `jsonschema` validating both schemas against valid and invalid payloads.

### 3. Technology Decisions & Alternatives Considered
- **Redpanda over Apache Kafka**: Selected Redpanda for its native C++ implementation, zero JVM overhead, instant startup, and predictable memory footprint ($1.5\text{ GB}$ vs. $\ge 3.0\text{ GB}$ for Kafka with ZooKeeper/KRaft).
- **JSON Schema Standard**: Used Draft-07 JSON Schema over binary Avro for development to allow direct inspection of message streams in REST clients and browser dashboards.

### 4. Files Created / Modified
- Created [`streaming/schemas/news_event_schema.json`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/streaming/schemas/news_event_schema.json)
- Created [`streaming/schemas/corporate_event_schema.json`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/streaming/schemas/corporate_event_schema.json)
- Created [`docs/architecture/streaming_architecture.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/architecture/streaming_architecture.md)
- Created [`tests/unit/test_streaming_schemas.py`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/tests/unit/test_streaming_schemas.py)
- Updated [`docs/PROJECT_TRACKER.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/PROJECT_TRACKER.md) (Step 3.7 marked APPROVED, Step 4.1 marked COMPLETED)
- Updated [`docs/CHANGELOG.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/CHANGELOG.md)
- Created [`docs/step_reports/phase_04_step_01_streaming_architecture.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/step_reports/phase_04_step_01_streaming_architecture.md)

### 5. Commands Executed & Testing Report
- Executed `python -m pytest tests/unit/test_streaming_schemas.py`
  - Output: `============================== 4 passed in 0.21s ==============================`
  - All 4 test cases passed:
    - `test_news_event_schema_validation_valid`: Verified valid `NewsEventMessage` serialization.
    - `test_news_event_schema_validation_missing_required`: Verified rejection when required fields are missing.
    - `test_corporate_event_schema_validation_valid`: Verified valid `CorporateEventMessage` serialization.
    - `test_corporate_event_schema_validation_invalid_symbol`: Verified rejection of empty symbol strings.

### 6. Known Limitations, Risks & Edge Cases
- Streaming broker containers will only be booted when running Phase 4 demonstration scripts, preventing idle memory usage during batch ML phases.

### 7. Reproduction Instructions & Status
Run `python -m pytest tests/unit/test_streaming_schemas.py`. Step 4.1 is **COMPLETED**.

---

### 8. Proposed Next Step
**Phase 4 — Step 4.2: Redpanda Broker Setup (Resource-Constrained Docker Profile)**
- Create the resource-capped Docker Compose service definition for Redpanda in `deployment/docker/docker-compose.streaming.yml` (under profile `streaming` with `mem_limit: 1.5g`).
- Create an automated broker initialization and topic provisioning script in `scripts/setup_streaming_topics.py` to create `news.events.raw` and `corporate.events.raw` with partition and retention policies.
- Deliverables: Compose manifest, topic provisioning script, and step report `docs/step_reports/phase_04_step_02_redpanda_setup.md`.
