# SYSTEM ARCHITECTURE & DESIGN SPECIFICATION
# MARKET SENTINEL AI
## AI-Powered Stock Market Surveillance and Risk Intelligence Platform

---

## Document Control
- **Document Version**: 1.0.0
- **Status**: APPROVED / BASELINE
- **Author**: Principal System Architect & Lead Product Owner
- **Single Source of Truth**: [`docs/MASTER_IMPLEMENTATION_PROMPT.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/MASTER_IMPLEMENTATION_PROMPT.md)
- **Operational Guidelines**: [`AGENTS.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/AGENTS.md)

---

## 1. Architectural Philosophy & Design Principles

Market Sentinel AI is engineered around five fundamental architectural tenets:

1. **Layered Separation of Concerns (SoC)**:
   - Presentation, application services, domain business logic, data access repositories, and external provider adapters are strictly decoupled.
2. **Hardware-Aware Containment**:
   - Designed to run within a **16 GB RAM, CPU-only** development footprint on Windows 11. Multi-service dependencies are organized into isolated Docker Compose profiles (`core`, `data`, `streaming`, `monitoring`) with hard memory quotas (`mem_limit`).
3. **Single System of Record with Vector Co-location**:
   - PostgreSQL 16+ is the single transactional source of truth. Vector embeddings for corporate filings and news disclosures reside directly in PostgreSQL via `pgvector`, eliminating the operational overhead and dual-write inconsistencies of a separate vector database.
4. **Provider-Decoupled Generative AI**:
   - LLM interactions route through an abstract provider interface (`LLMProviderInterface`). Groq API is the baseline implementation; future migrations to OpenAI, Gemini, or local models require zero changes to business logic.
5. **Zero Look-Ahead Bias & Auditability**:
   - Data storage, feature computation, and model inference pipelines maintain strict chronological lineage. Every generated risk alert stores an immutable snapshot of triggering feature values, model versions, and source timestamps.

---

## 2. C4 Architecture Level 1: System Context Diagram

The System Context diagram illustrates how Market Sentinel AI integrates into the broader financial market ecosystem, interacts with external data sources, and serves distinct user roles.

```mermaid
flowchart TD
    subgraph ExternalSources["External Data & Intelligence Feeds"]
        E1["Market Data Feeds<br/>(NSE Reports / Alpha Vantage)"]
        E2["Corporate Disclosure Feeds<br/>(Exchange Filings / SEC EDGAR)"]
        E3["Financial News Feeds<br/>(Legitimate News APIs / RSS)"]
        E4["Remote LLM Provider<br/>(Groq Cloud API)"]
    end

    subgraph Platform["Market Sentinel AI Platform"]
        MS["Market Sentinel AI System<br/>(Surveillance, Risk Scoring & RAG)"]
    end

    subgraph UserRoles["Surveillance & Risk Team"]
        U1["Sarah: Head of Compliance<br/>(Audit Trails, Regulatory SARs)"]
        U2["David: Quantitative Risk Manager<br/>(Volatility Clustering, Margin Cuts)"]
        U3["Priya: Surveillance Analyst<br/>(Alert Triage, Evidence Review)"]
    end

    E1 -->|"Daily / Intraday OHLCV & Delivery"| MS
    E2 -->|"Corporate Actions & Filings"| MS
    E3 -->|"Public Financial Articles"| MS
    MS <-->|"Prompt & Evidence Dossier Retrieval"| E4

    MS -->|"High-Priority Escalations & Audit Logs"| U1
    MS -->|"Real-time Volatility & Anomaly Signals"| U2
    MS -->|"Investigation Dossiers & Dispositions"| U3
    U3 -->|"Case Notes & Disposition Actions"| MS
```

---

## 3. C4 Architecture Level 2: Container Architecture & Service Profiles

To respect the **16 GB RAM limit**, containers are partitioned into four modular Docker Compose profiles. Users only boot the profiles required for the active operational workload.

```mermaid
flowchart TB
    subgraph Browser["User Workspace"]
        SPA["Frontend SPA<br/>(React + TypeScript + Tailwind CSS)<br/>Port: 3000"]
    end

    subgraph ProfileCore["Profile: 'core' (Always Active)"]
        API["Backend API Service<br/>(FastAPI / Python 3.10+)<br/>Port: 8000 | Limit: 1.5 GB"]
        PG[("Primary Database<br/>PostgreSQL 16 + pgvector<br/>Port: 5432 | Limit: 2.0 GB")]
        REDIS[("Caching & Transient State<br/>Redis 7.x<br/>Port: 6379 | Limit: 512 MB")]
    end

    subgraph ProfileData["Profile: 'data' (Batch Operations Only)"]
        AF_SCHED["Airflow Scheduler<br/>Limit: 1.0 GB"]
        AF_WEB["Airflow Webserver<br/>Port: 8080 | Limit: 1.0 GB"]
        PARQUET[("Analytical Storage<br/>Columnar Parquet Files<br/>Local Filesystem / S3")]
    end

    subgraph ProfileStreaming["Profile: 'streaming' (Event Demos Only)"]
        RP["Redpanda Broker<br/>(Kafka-compatible)<br/>Port: 9092 | Limit: 1.5 GB"]
        SPARK["Apache Spark<br/>(Single-node Stream Worker)<br/>Limit: 2.0 GB"]
    end

    subgraph ProfileMonitoring["Profile: 'monitoring' (Observability Only)"]
        PROM["Prometheus Server<br/>Port: 9090 | Limit: 512 MB"]
        GRAF["Grafana Dashboards<br/>Port: 3001 | Limit: 512 MB"]
        ALERT_MGR["Alertmanager<br/>Port: 9093 | Limit: 256 MB"]
    end

    SPA -->|"REST APIs / JSON"| API
    SPA -->|"SSE (Real-time Alerts)"| API
    API -->|"Relational Queries & Vector Search"| PG
    API -->|"Session Cache & Token Limiting"| REDIS
    API -->|"Query Feature Baselines"| PARQUET

    AF_SCHED -->|"Trigger Batch Pipelines"| API
    AF_SCHED -->|"Persist Clean Datasets"| PG
    AF_SCHED -->|"Write Feature Snapshots"| PARQUET

    RP -->|"Consume Event Streams"| SPARK
    SPARK -->|"Sink Processed Events"| PG
    SPARK -->|"Append Event Logs"| PARQUET

    API -->|"Expose /metrics"| PROM
    PROM -->|"Scrape Metrics"| GRAF
    PROM -->|"Trigger Alerts"| ALERT_MGR
```

---

## 4. C4 Architecture Level 3: Backend Component Architecture

The backend adheres to a clean layered architecture within FastAPI:

```mermaid
flowchart TD
    subgraph Presentation["Presentation & Routing Layer (FastAPI Routers)"]
        R_AUTH["Auth Router<br/>(/api/v1/auth)"]
        R_MARKET["Market Data Router<br/>(/api/v1/market)"]
        R_ANOMALY["Anomaly & Vol Router<br/>(/api/v1/analytics)"]
        R_NEWS["News & Events Router<br/>(/api/v1/news)"]
        R_ALERT["Alerts & Dossier Router<br/>(/api/v1/alerts)"]
        R_SSE["SSE Notification Router<br/>(/api/v1/events)"]
    end

    subgraph Application["Application Business Logic Layer (Services)"]
        S_INGEST["Ingestion Service<br/>(Validation & Normalization)"]
        S_ANOMALY["Anomaly Detection Service<br/>(Z-Score + Isolation Forest)"]
        S_VOL["Volatility Service<br/>(EWMA + GARCH Forecast)"]
        S_NLP["NLP Intelligence Service<br/>(NER + Event Classifier)"]
        S_CORR["Risk Scoring Engine<br/>(Multi-Factor Correlation)"]
        S_RAG["RAG Orchestrator<br/>(pgvector + Prompt Synthesis)"]
    end

    subgraph Abstraction["Provider & Integration Layer"]
        P_LLM["LLM Provider Interface<br/>(Groq Adapter / Fallbacks)"]
        P_DATA["Market Data Client<br/>(NSE / Alpha Vantage)"]
        P_EMBED["Embedding Client<br/>(CPU-Optimized SentenceTransformer)"]
    end

    subgraph DataAccess["Persistence & Repository Layer"]
        REPO_MKT["Market Repository"]
        REPO_ALERT["Alert Repository"]
        REPO_DOC["Document & Vector Repository"]
        REPO_AUDIT["Audit & Disposition Repository"]
    end

    R_MARKET --> S_INGEST
    R_ANOMALY --> S_ANOMALY
    R_ANOMALY --> S_VOL
    R_NEWS --> S_NLP
    R_ALERT --> S_CORR
    R_ALERT --> S_RAG

    S_INGEST --> P_DATA
    S_INGEST --> REPO_MKT
    S_ANOMALY --> REPO_MKT
    S_VOL --> REPO_MKT
    S_NLP --> REPO_DOC
    S_CORR --> REPO_MKT
    S_CORR --> REPO_DOC
    S_CORR --> REPO_ALERT
    S_RAG --> P_EMBED
    S_RAG --> REPO_DOC
    S_RAG --> P_LLM
    S_RAG --> REPO_ALERT
```

---

## 5. End-to-End Data Flow Diagrams

### 5.1 Batch Data Ingestion & Feature Engineering Flow
Orchestrated via Apache Airflow on daily/scheduled triggers:

```mermaid
sequenceDiagram
    autonumber
    actor Scheduler as Airflow Scheduler
    participant Ingest as Market Ingestion Service
    participant Validator as Quality Validation Engine
    participant DB as PostgreSQL (Timeseries)
    participant FeatStore as Parquet Storage
    participant FeatureEng as Feature Computation Engine

    Scheduler->>Ingest: Trigger Daily Batch Run (Date T)
    Ingest->>Ingest: Fetch Official Exchange Reports (OHLCV + Delivery)
    Ingest->>Validator: Validate Schema, Non-Zero Prices & Volumes
    Validator-->>Ingest: Data Cleansed & Validated
    Ingest->>DB: Upsert Clean Market Records (Audit Lineage Logged)
    Scheduler->>FeatureEng: Compute Rolling Features (T-20 to T)
    FeatureEng->>DB: Read Chronological Window (No Look-Ahead)
    FeatureEng->>FeatureEng: Calculate Returns, Volatility, Volume Z-Scores
    FeatureEng->>FeatStore: Persist Immutable Parquet Feature Snapshots
    Scheduler-->>Scheduler: Task Run Completed Successfully
```

### 5.2 Anomaly Detection, Volatility Modeling & Risk Scoring Flow
Transforms raw market features into prioritized investigation alerts:

```mermaid
sequenceDiagram
    autonumber
    participant Engine as Surveillance Engine
    participant Baselines as Statistical Baselines (Z-Score)
    participant IsoForest as Isolation Forest Model
    participant GARCH as Volatility Model (GARCH/EWMA)
    participant NLP as News & Corporate Event Store
    participant RiskScorer as Risk Scoring Matrix
    participant DB as PostgreSQL Alert Store
    participant SSE as SSE Broadcast Hub

    Engine->>Baselines: Evaluate Price Return & Volume Z-Scores
    Engine->>IsoForest: Predict Multi-Variate Anomaly Score
    Engine->>GARCH: Forecast 5-Day Volatility Cluster
    Engine->>NLP: Query Events in Window [T-48h, T+24h]
    NLP-->>Engine: Return Mapped Company Filings & News Spikes
    Engine->>RiskScorer: Synthesize Composite Risk Score (0-100)
    RiskScorer->>RiskScorer: Determine Priority (Critical, High, Medium, Low)
    RiskScorer->>DB: Save Alert Record (Feature Vector + Metadata)
    opt If Priority is High or Critical (Score >= 70)
        RiskScorer->>SSE: Emit 'New Alert' Event to Connected Browsers
    end
```

### 5.3 Evidence-Grounded RAG Investigation Dossier Flow
Enforces zero hallucination and evidence citations:

```mermaid
sequenceDiagram
    autonumber
    actor Analyst as Surveillance Analyst
    participant UI as React Dashboard
    participant API as FastAPI Alerts Endpoint
    participant RAG as RAG Service
    participant PGVec as pgvector (PostgreSQL)
    participant LLM as Groq LLM Adapter

    Analyst->>UI: Click on Alert (Symbol: TATAMOTORS, Date: T)
    UI->>API: GET /api/v1/alerts/{alert_id}/dossier
    API->>RAG: Generate Investigation Dossier
    RAG->>PGVec: Query Chunks (Symbol Match + Temporal Window + Cosine Similarity)
    PGVec-->>RAG: Return Top-K Ranked Context Chunks
    alt No Context Chunks Pass Similarity Threshold
        RAG-->>API: Return "Insufficient evidence found in official disclosures."
        API-->>UI: Display Alert with Missing Information Notice
    else Context Chunks Available
        RAG->>LLM: Generate Dossier (System Prompt + Structured Evidence + Strict Citations)
        LLM-->>RAG: Structured JSON Response (Summary, Signals, Citations, Next Steps)
        RAG->>API: Return Formatted Investigation Dossier
        API-->>UI: Render Dossier with Clickable Source Links
    end
    Analyst->>UI: Select Disposition ("Escalate to Compliance") & Enter Case Notes
    UI->>API: POST /api/v1/alerts/{alert_id}/disposition
    API->>PGVec: Append Immutable Audit Record
```

---

## 6. Security, Authentication & Session Architecture

- **Stateless Authentication**: JSON Web Tokens (JWT) using HMAC-SHA256 (`HS256`).
- **Role-Based Access Control (RBAC)**:
  - `Analyst`: View monitors, inspect alerts, review RAG dossiers, add investigation notes, dismiss low/medium alerts.
  - `Senior Compliance Officer`: All Analyst permissions + escalate alerts, export official SAR packages, configure scoring weights.
  - `System Admin`: Manage user accounts, trigger pipeline re-runs, inspect system metrics.
- **Credential Storage**: Passwords hashed using `bcrypt` with salt rounds $\ge 12$. Secrets loaded via environment variables; never committed to Git.
