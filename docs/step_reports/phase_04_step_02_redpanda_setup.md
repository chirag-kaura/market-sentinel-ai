# STEP IMPLEMENTATION REPORT
## Phase 4 — Step 4.2: Redpanda Broker Setup (Resource-Constrained)
**Project**: Market Sentinel AI  
**Date**: 2026-11-17  
**Status**: COMPLETED (Awaiting User Sign-Off)

---

### 1. Objective & Business Relevance
- **Objective**: Author a resource-conscious Docker Compose service definition deploying a single-broker Redpanda instance (Kafka API compatible) and Redpanda Console web UI under the `streaming` profile with strict memory limits ($1.5\text{ GB}$), alongside an automated topic provisioning script creating partitioned topics (`news.events.raw`, `corporate.events.raw`, `news.intensity.spikes`).
- **Business Relevance**: Supplies the high-throughput, low-latency streaming broker required to ingest live financial news and regulatory filings in real time while strictly preventing host memory crashes on the 16 GB development machine.

### 2. Technical Explanation & Architectural Fit
- Implemented [`deployment/docker/docker-compose.streaming.yml`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/deployment/docker/docker-compose.streaming.yml):
  - Service `redpanda`: Image `docker.redpanda.com/redpandadata/redpanda:v24.2.14`, assigned strictly to profile `streaming`.
  - Memory & CPU bounds: `mem_limit: 1536m` ($1.5\text{ GB}$) and `cpus: 1.5`, executing with `--smp 1 --memory 1G --reserve-memory 0M`.
  - Ports exposed: `19092` (host external Kafka client port), `9092` (internal Docker network port), `8081` (schema registry), `8082` (REST proxy).
  - Health check: `rpk cluster health` polling every 10 seconds.
  - Service `redpanda-console`: Lightweight web dashboard on port `8085` capped at `256m` RAM.
- Implemented [`scripts/setup_streaming_topics.py`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/scripts/setup_streaming_topics.py):
  - Connects to Kafka broker via `KafkaAdminClient`.
  - Automatically provisions:
    - `news.events.raw`: 3 partitions, replication factor 1, 7-day retention ($604,800,000\text{ ms}$).
    - `corporate.events.raw`: 3 partitions, replication factor 1, 30-day retention ($2,592,000,000\text{ ms}$).
    - `news.intensity.spikes`: 1 partition, replication factor 1, 3-day retention ($259,200,000\text{ ms}$).
  - Fallback: Graceful offline simulation when broker container is inactive.
- Authored automated unit test suite `tests/unit/test_streaming_setup.py` verifying Compose syntax, resource constraints, topic configurations, and provisioning function.

### 3. Technology Decisions & Alternatives Considered
- **Redpanda Developer Mode (`--mode dev-container`)**: Configured specifically for single-node development on laptops, disabling expensive distributed quorum overhead.
- **Port Disambiguation**: Exposes Kafka client traffic on port `19092` to avoid conflicts with any existing default Kafka ports on developer machines.

### 4. Files Created / Modified
- Created [`deployment/docker/docker-compose.streaming.yml`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/deployment/docker/docker-compose.streaming.yml)
- Created [`scripts/setup_streaming_topics.py`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/scripts/setup_streaming_topics.py)
- Created [`tests/unit/test_streaming_setup.py`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/tests/unit/test_streaming_setup.py)
- Updated [`docs/PROJECT_TRACKER.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/PROJECT_TRACKER.md) (Step 4.1 marked APPROVED, Step 4.2 marked COMPLETED)
- Updated [`docs/CHANGELOG.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/CHANGELOG.md)
- Created [`docs/step_reports/phase_04_step_02_redpanda_setup.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/step_reports/phase_04_step_02_redpanda_setup.md)

### 5. Commands Executed & Testing Report
- Executed `python -m pytest tests/unit/test_streaming_setup.py`
  - Output: `============================== 3 passed in 2.61s ==============================`
  - All 3 test cases passed:
    - `test_streaming_compose_manifest_structure`: Verified Redpanda container configuration, profile `streaming`, and memory limit $1.5\text{ GB}$.
    - `test_topic_configs_specification`: Verified partition counts and retention ms parameters.
    - `test_provision_topics_dry_run`: Verified offline execution and error handling.

### 6. Known Limitations, Risks & Edge Cases
- When running Redpanda under Docker Desktop on Windows 11, WSL 2 memory limits should be respected; the Compose manifest explicitly caps memory at $1.5\text{ GB}$.

### 7. Reproduction Instructions & Status
Run `python -m pytest tests/unit/test_streaming_setup.py`. Step 4.2 is **COMPLETED**.

---

### 8. Proposed Next Step
**Phase 4 — Step 4.3: Streaming Event Producers (News & Corporate Filings)**
- Implement robust streaming event producers in `streaming/producers/`:
  - `news_event_producer.py`: Consumes parsed RSS articles, maps detected stock tickers, validates against `NewsEventMessage` schema, and publishes to `news.events.raw` using primary symbol as message key.
  - `corporate_event_producer.py`: Publishes corporate announcements to `corporate.events.raw` using symbol as message key.
  - Implement retry policies, connection pooling, and offline buffering.
  - Write automated unit tests in `tests/unit/test_event_producers.py`.
- Deliverables: Producer modules and unit test suite.
