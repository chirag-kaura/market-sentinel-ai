# Market Sentinel AI — Master Technical Architecture & Specification

## 1. Project Overview & Governance
Market Sentinel AI is an enterprise AI-powered stock market surveillance and risk intelligence decision-support platform designed to assist compliance officers and analysts in detecting unusual trading patterns, market manipulation signals, and pre-announcement trading anomalies.

- **Single Source of Truth**: `docs/MASTER_IMPLEMENTATION_PROMPT.md`
- **Governance Rules**: `AGENTS.md`
- **Development Profile**: Windows 11, 16 GB RAM, CPU-Only Execution, Docker Desktop (WSL 2)

---

## 2. End-to-End System Architecture

```
[ Market Data & News Ingestion ]
           │
           ▼
[ Feature Engineering & GARCH Volatility ] ──► [ Isolation Forest Anomaly Detection ]
           │                                                    │
           └──────────────────────────┬─────────────────────────┘
                                      ▼
                        [ Market-News Temporal Correlation ]
                                      │
                                      ▼
                        [ Hybrid Dense Vector RAG (pgvector) ]
                                      │
                                      ▼
                        [ Grounded Investigation Dossier (Groq) ]
                                      │
                                      ▼
                   [ FastAPI REST & SSE Real-Time Streaming ]
                                      │
                                      ▼
             [ React + TypeScript + Tailwind Surveillance Workspace ]
```

---

## 3. Layer Specifications

### Layer 1: Data Engineering & Batch Ingestion (Phase 2 & 3)
- Canonical symbol master reference (`data/master/symbol_master.parquet`).
- Ingestion pipelines for market ticks, news feeds, and corporate disclosures.
- Idempotent Airflow orchestration DAGs (`orchestration/airflow/dags/`).

### Layer 2: Real-time Event Streaming (Phase 4)
- Redpanda single-broker streaming with bounded memory limits (`1280M`).
- News spike and volume surge detection consumers with Parquet analytical sink persistence.

### Layer 3: Feature Engineering & Statistical Modeling (Phase 5 & 6)
- Statistical baselines: Rolling z-scores, percentile ranks, GARCH(1,1) conditional volatility.
- Machine Learning: Multi-feature Isolation Forest with chronological walk-forward cross-validation.
- Zero look-ahead bias and strict point-in-time data isolation.

### Layer 4: NLP & News Intelligence (Phase 7)
- Text cleaning, entity recognition, ticker disambiguation, corporate event classification, financial sentiment scoring, and news novelty decay estimation.

### Layer 5: Market-News Correlation Engine (Phase 8)
- Dynamic lead-lag temporal alignment windows ($\Delta t \in [-48\text{h}, +12\text{h}]$).
- Composite risk scoring formula:
  $$\text{Risk Score} = 0.35 \cdot S_{\text{price}} + 0.25 \cdot S_{\text{volume}} + 0.25 \cdot S_{\text{sentiment}} + 0.15 \cdot S_{\text{novelty}}$$
- Quality audit and backtesting harness with deterministic alert prioritization.

### Layer 6: Generative AI, RAG & Evidence Grounding (Phase 9)
- Chunking, hybrid dense vector search with recency decay scoring.
- Zero-hallucination audit engine enforcing strict factual support in retrieved corporate filings.
- Token budgeting and LRU cache controller for cloud LLM cost optimization.

### Layer 7: Full-Stack Application & Workspace (Phase 10)
- FastAPI ASGI backend with global exception handling, correlation ID middleware, connection pooling, and JWT role-based access control.
- Server-Sent Events (SSE) `/api/v1/stream/alerts` push streaming.
- Type-safe React + TypeScript + Tailwind dark terminal surveillance workspace.

### Layer 8: Enterprise Observability & Packaging (Phase 11 & 12)
- Structured JSON logging with `X-Correlation-ID` request tracking.
- Prometheus `/metrics` exposition and declarative Grafana dashboards.
- Statistical Kolmogorov-Smirnov and PSI data drift monitoring.
- Multi-profile Docker Compose (`core`, `streaming`, `monitoring`) and Kubernetes manifests.
