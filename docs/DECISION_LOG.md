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
