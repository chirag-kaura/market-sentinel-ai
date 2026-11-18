# STEP IMPLEMENTATION REPORT
## Phase 1 — Step 1.3: Product Scope & Boundary Definition
**Project**: Market Sentinel AI  
**Date**: 2026-11-17  
**Status**: COMPLETED (Awaiting User Sign-Off)

---

### 1. Objective & Business Relevance
- **Objective**: Formally demarcate what is in-scope for the Minimum Viable Product (MVP), what constitutes extended/demonstrative capabilities, and what is strictly out-of-scope. Identify dependencies, assumptions, and a risk register with actionable mitigations.
- **Business Relevance**: Prevents scope creep, protects hardware stability on the 16 GB RAM host, and ensures the product maintains strict regulatory and academic boundaries (decision-support only, zero synthetic stock data, zero trading bot functionality).

### 2. Technical Explanation & Architectural Fit
- Created [`docs/business/product_scope.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/business/product_scope.md) covering:
  - **In-Scope MVP**: Batch market data ingestion (OHLCV + delivery), PostgreSQL 16+ with `pgvector`, Parquet feature store, Airflow DAGs, statistical Z-score/IQR baselines, Isolation Forest anomaly detection, EWMA/GARCH volatility intelligence, news NLP (NER, event classification, sentiment), multi-factor risk scoring, Groq LLM RAG dossier generation, React/TypeScript/Tailwind dashboard, and Prometheus/Grafana/Evidently monitoring.
  - **In-Scope Extended Capabilities**: Single-broker Redpanda event streaming, targeted Apache Spark Structured Streaming, SSE real-time notifications, and Minikube K8s demonstration manifests.
  - **Strictly Out-of-Scope**: Automated trade execution/bots, investment advice/price direction calls, automated legal fraud accusations, synthetic market data fabrication, local 7B+ LLM hosting, and unauthorized paywall scraping.
  - **Risk Register**: 6 concrete risks (RSK-01 to RSK-06) covering hardware constraints, data rate limits, hallucination, look-ahead bias, API cost, and entity-ticker alignment, mapped to actionable mitigations.

### 3. Technology Decisions & Alternatives Considered
- **Docker Compose Profiles**: Confirmed as the primary mechanism to mitigate RSK-01 (host memory exhaustion).
- **Batch-First MVP**: Prioritized over full real-time tick streaming to guarantee authentic data integrity and prevent synthetic simulation.

### 4. Files Created / Modified
- Created [`docs/business/product_scope.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/business/product_scope.md)
- Updated [`docs/PROJECT_TRACKER.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/PROJECT_TRACKER.md) (Step 1.2 marked APPROVED, Step 1.3 marked COMPLETED)
- Updated [`docs/CHANGELOG.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/CHANGELOG.md)
- Created [`docs/step_reports/phase_01_step_03_product_scope.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/step_reports/phase_01_step_03_product_scope.md)

### 5. Commands Executed & Testing Report
- Verified internal hyperlinks, cross-references with `BRD.md` and `MASTER_IMPLEMENTATION_PROMPT.md`.
- Audited risk mitigation strategies against hardware profile constraints (16 GB RAM / CPU-only).

### 6. Known Limitations, Risks & Edge Cases
- If external news APIs enforce tight free-tier rate limits, local caching in Parquet and mock API testing adapters will be utilized during development without affecting production code integrity.

### 7. Reproduction Instructions & Status
All files are saved in `docs/` and tracked in Git. Step 1.3 is **COMPLETED**.

---

### 8. Proposed Next Step
**Phase 1 — Step 1.4: Functional Architecture & System Diagrams**
- Design system context diagram (C4 Level 1), container architecture (C4 Level 2), and component architecture (C4 Level 3).
- Model end-to-end data flow diagrams for batch pipelines, event streaming, ML/NLP feature loops, RAG investigation loops, and analyst workflows using Mermaid.
- Deliverable: `docs/architecture/system_architecture.md`.
