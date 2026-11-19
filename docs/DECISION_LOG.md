# ARCHITECTURE & TECHNOLOGY DECISION LOG (ADR)
# MARKET SENTINEL AI

---

## ADR-001: Adoption of Mandatory 12-Phase Baby-Step Execution Protocol
- **Date**: 2026-11-17
- **Status**: ACCEPTED
- **Context**: The project is a comprehensive postgraduate Data Science and Generative AI capstone requiring full production-grade rigor across financial analytics, data engineering, distributed streaming, ML, NLP, RAG, and DevOps. Large-scale monolithic generation would risk hallucinations, untested code, and system unreliability.
- **Alternatives Considered**:
  - Full-codebase scaffolding in a single pass.
  - Informal ad-hoc development.
- **Decision**: Adopt the 12-phase, granular baby-step implementation protocol codified in [`docs/MASTER_IMPLEMENTATION_PROMPT.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/MASTER_IMPLEMENTATION_PROMPT.md) and [`AGENTS.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/AGENTS.md).
- **Consequences**: Every step must have a pre-implementation plan, rigorous unit/integration tests, step documentation, and approval gates before advancing.

---

## ADR-002: Development Environment & Hardware-Aware Architecture Baseline
- **Date**: 2026-11-17
- **Status**: ACCEPTED
- **Context**: Development is hosted on a Windows 11 machine with 16 GB shared RAM, Intel x86_64 CPU, and **no dedicated GPU**.
- **Alternatives Considered**:
  - Running local 7B+ LLMs via Ollama or vLLM.
  - Booting all infrastructure containers simultaneously (Airflow, Redpanda, Spark, Minikube, Prometheus, Grafana).
- **Decision**:
  1. Ban local heavy LLM instances; route all Generative AI inference through an external provider abstraction (Groq API as baseline).
  2. Implement segmented Docker Compose profiles (`core`, `data`, `streaming`, `monitoring`) with strict container CPU and memory quotas (`mem_limit`).
  3. Restrict Apache Spark and Redpanda to isolated, dedicated demonstration phases.
- **Consequences**: High memory headroom is preserved for the OS and IDE; eliminates out-of-memory container crashes.

---

## ADR-003: Vector Search Architecture — PostgreSQL `pgvector`
- **Date**: 2026-11-17
- **Status**: ACCEPTED
- **Context**: The system requires vector semantic search for corporate filings and news disclosures to support evidence-grounded RAG.
- **Alternatives Considered**:
  - Standalone vector databases (Pinecone, Milvus, Chroma, Qdrant).
- **Decision**: Use the `pgvector` extension within PostgreSQL 16+.
- **Rationale**: PostgreSQL is already the primary relational database of record. Introducing an external vector database adds unneeded architectural complexity, operational overhead, and dual-write consistency issues. `pgvector` provides high-performance cosine similarity within the existing transactional database.
- **Consequences**: Eliminates extra container overhead and external SaaS subscription dependencies.

---

## ADR-004: Ingestion Client Resilient Network Architecture, Provenance & Licensing Matrix
- **Date**: 2026-11-18
- **Status**: ACCEPTED
- **Context**: Ingestion clients for NSE Bhavcopy, NSE Delivery, and SEC EDGAR parsed file formats but lacked direct HTTP download logic and automated exponential backoff retries. Corporate disclosure timestamps also misclassified Indian Standard Time (IST) as UTC.
- **Alternatives Considered**:
  - Ad-hoc urllib requests without structured retry policies.
  - Relying on manual operator downloads.
- **Decision**:
  1. Standardize on `httpx` with timeout management and streaming downloads across all ingestion clients.
  2. Implement an automated Tenacity-backed retry decorator (`ingestion_retry`) targeting HTTP 429, 502, 503, 504 and transient network disconnects with exponential backoff and jitter.
  3. Enforce UTC conversion for Indian market announcements using `zoneinfo.ZoneInfo("Asia/Kolkata")`.
  4. Persist end-to-end cryptographic provenance (`retrieval_timestamp_utc`, `original_source_url`, `content_hash`).
  5. Establish a 4-Tier Data Licensing Matrix in `docs/licensing_matrix.md` distinguishing statutory disclosures from restricted exchange commercial data.
- **Consequences**: Eliminates ingestion interruptions due to rate limits or transient outages; protects against timestamp drift in temporal correlation; aligns with regulatory licensing requirements.

---

## ADR-028: Remediation of 50 Priority Failures & Zero Synthetic Data Production Ingestion
- **Date**: 2026-11-19
- **Status**: ACCEPTED
- **Context**: Comprehensive audit revealed 50 priority architectural and security vulnerabilities spanning unauthenticated REST endpoints, in-memory case storage, static SSE replay, look-ahead bias in rolling feature windows, lack of circuit breaking, and mock data masquerading as live operational state.
- **Alternatives Considered**:
  - Incremental remediation without architectural standardization.
  - Generating synthetic fixture data to simulate scale.
- **Decision**:
  1. **Strict Zero Synthetic Financial Data Directive**: Mandated that all operational market data stored in PostgreSQL/SQLite must originate from genuine exchange quotes and official corporate news feeds.
  2. **Security & RBAC Enforcement**: Enforced PBKDF2 with unique cryptographic random salts and 100,000 iterations, with 4 institutional personas (`READ_ONLY_ANALYST`, `ANALYST`, `COMPLIANCE_OFFICER`, `ADMIN`) guarding critical endpoints via `Depends(get_current_user)`.
  3. **Persistent Investigation & Audit Dispositions**: Replaced in-memory case variables with persistent database models (`InvestigationCaseModel`, `AnalystDispositionModel`) supporting status transitions, note logging, escalation, and dismissal.
  4. **Dynamic Event-Driven SSE Broker**: Replaced static replay with `AlertStreamBroker` enabling asynchronous real-time streaming to connected web clients.
  5. **Causal Point-in-Time Integrity**: Enforced strict `.shift(1)` on all 20-day rolling baseline means and standard deviations, eliminating look-ahead bias.
  6. **Blocking Grounding Gate & Prompt Injection Defense**: Integrated blocking hallucination audits and sanitized untrusted media text inside XML `<context>` tags.
- **Consequences**: 100% of unit and integration tests (230 tests) pass cleanly. Complete operational compliance with BRD, architectural specifications, and ethical integrity standards.
