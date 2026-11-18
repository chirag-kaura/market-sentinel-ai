# TECHNOLOGY DECISION RECORDS (TDR / ADR)
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

## 1. Governance & Evaluation Framework

Every technology selected for **Market Sentinel AI** is evaluated against five concrete architectural criteria:
1. **Business Fit**: Does the technology directly solve a concrete requirement in the surveillance and risk intelligence lifecycle?
2. **Hardware Feasibility**: Can the tool run reliably within a **16 GB RAM, CPU-only** environment on Windows 11 without degrading operating system stability?
3. **Zero Financial Licensing Cost**: Is the solution open-source or free-tier compliant, avoiding commercial enterprise licensing?
4. **Maintainability & Type Safety**: Does it support modular architecture, static typing, and automated testing?
5. **No Redundancy**: Does it eliminate duplicate storage or operational layers (e.g. co-locating relational and vector data)?

---

## 2. Master Technology Decision Records

### TDR-01: Frontend Framework — React + TypeScript + Tailwind CSS
- **Requirement**: Build a responsive, modular financial surveillance dashboard featuring real-time alert queues, interactive candlestick charts with anomaly markers, AI investigation dossiers, and audit workflows.
- **Selected Technology**: **React 18+ with TypeScript and Tailwind CSS**.
- **Alternatives Considered**:
  - *Angular*: Enterprise-grade, but heavy bundle size, high boilerplate, and rigid opinionated conventions that slow prototyping.
  - *Vue.js*: Lightweight and intuitive, but smaller institutional financial ecosystem and less prevalent in production trading desks.
  - *Vanilla JS / Streamlit*: Streamlit re-executes the entire script on state changes, causing chart flickering, sluggish interactions, and severe limitations for complex multi-pane surveillance cockpits.
- **Rationale**: React with strict TypeScript eliminates `any` type sprawl, provides a rich ecosystem of financial charting libraries (Lightweight Charts / Recharts), and enables modular, componentized UI design. Tailwind CSS enables rapid, consistent styling without CSS bloat.
- **Hardware Overhead & Cost**: Zero server footprint; executes client-side in the analyst's browser. Zero licensing cost (MIT).

---

### TDR-02: Backend API Framework — FastAPI (Python 3.10+)
- **Requirement**: High-performance, asynchronous REST API layer to serve market queries, execute anomaly scoring pipelines, stream real-time SSE notifications, and interface with LLM providers.
- **Selected Technology**: **FastAPI**.
- **Alternatives Considered**:
  - *Django*: Mature ORM and admin panel, but monolithic, opinionated, heavy memory footprint, and historically synchronous architecture.
  - *Flask*: Lightweight, but lacks native async/await concurrency, requires manual Pydantic integration, and lacks automatic OpenAPI schema generation.
  - *Node.js (Express/NestJS)*: Excellent async I/O, but segregates backend services from Python's rich data science, machine learning, and statistical ecosystem (Pandas, Scikit-learn, Statsmodels, Arch).
- **Rationale**: FastAPI provides native async concurrency, automatic OpenAPI documentation, strict Pydantic data validation, high throughput, and seamless in-process execution of Python ML/statistical pipelines.
- **Hardware Overhead & Cost**: Lightweight memory footprint ($\approx 150-300\text{ MB}$); container memory capped at $1.5\text{ GB}$. Open source (MIT).

---

### TDR-03: Primary Database — PostgreSQL 16+
- **Requirement**: ACID-compliant, robust relational storage for company master data, historical daily/intraday OHLCV market records, corporate disclosures, alert logs, and analyst audit dispositions.
- **Selected Technology**: **PostgreSQL 16+**.
- **Alternatives Considered**:
  - *MySQL*: Strong relational support, but weaker JSON manipulation, inferior window function performance, and lacks native vector search extensions comparable to `pgvector`.
  - *MongoDB*: Document database flexibility, but lacks native ACID guarantees across complex relational joins (essential for corporate filing and price correlation) and increases data integrity risk.
- **Rationale**: PostgreSQL is the gold standard for financial data integrity, offering robust indexing (B-Tree, BRIN for timeseries), partition support, window functions, and native JSONB capabilities.
- **Hardware Overhead & Cost**: Highly tunable memory footprint; container capped at $2.0\text{ GB}$. Open source (PostgreSQL License).

---

### TDR-04: Vector Search Architecture — PostgreSQL `pgvector`
- **Requirement**: Store dense vector embeddings of corporate announcements and financial news articles to perform semantic similarity retrieval for RAG-driven investigation dossiers.
- **Selected Technology**: **`pgvector` Extension within PostgreSQL 16+**.
- **Alternatives Considered**:
  - *Standalone Vector DBs (Pinecone, Milvus, Chroma, Qdrant)*: Introducing a dedicated vector database forces dual-write operations, distributed consistency issues, additional container memory overhead ($1-2\text{ GB}$), or reliance on proprietary cloud SaaS APIs with subscription costs.
- **Rationale**: `pgvector` co-locates relational corporate filings with their vector embeddings within PostgreSQL. This enables single-query hybrid filtering (e.g. filter by `symbol = 'TATAMOTORS'`, `published_at BETWEEN ...`, and cosine similarity distance) with zero additional container overhead.
- **Hardware Overhead & Cost**: Reuses existing PostgreSQL memory allocation; zero incremental infrastructure cost. Open source (PostgreSQL License).

---

### TDR-05: Caching & Transient State — Redis 7.x
- **Requirement**: Fast in-memory caching for active analyst sessions, LLM prompt/response caching (preventing redundant external API costs), and rate-limiting counters.
- **Selected Technology**: **Redis 7.x**.
- **Alternatives Considered**:
  - *Memcached*: Simple key-value store, but lacks data persistence, advanced data structures (sets, hashes), and Pub/Sub primitives.
  - *In-Memory Python Dicts*: Non-persistent across worker processes; fails when scaling API workers or during container restarts.
- **Governance Rule**: Redis is strictly a cache and transient buffer; **PostgreSQL is the sole system of record**.
- **Hardware Overhead & Cost**: Extremely low memory consumption; capped at $512\text{ MB}$. Open source (BSD/RSAL).

---

### TDR-06: Batch Workflow Orchestration — Apache Airflow
- **Requirement**: Scheduled, idempotent orchestration of daily market data ingestion, data quality audits, feature engineering pipelines, and model monitoring workflows.
- **Selected Technology**: **Apache Airflow 2.x**.
- **Alternatives Considered**:
  - *Cron Jobs*: No DAG dependency graph, no automatic retries with exponential backoff, no task lineage, and zero execution UI.
  - *Prefect / Dagster*: Modern, but Airflow remains the ubiquitous industry-standard orchestration tool across financial institutions and compliance desks.
- **Governance Rule**: Airflow is isolated to the `data` Docker Compose profile. It is triggered only during scheduled batch runs or testing, never run continuously alongside heavy streaming services.
- **Hardware Overhead & Cost**: Capped at $1.0\text{ GB}$ each for scheduler and webserver. Open source (Apache 2.0).

---

### TDR-07: Event Streaming Broker — Redpanda (Single-Broker)
- **Requirement**: High-throughput, Kafka-compatible event streaming broker to ingest and transport incoming news events and corporate disclosure streams in real time.
- **Selected Technology**: **Redpanda (Single-Broker, Kafka API Compatible)**.
- **Alternatives Considered**:
  - *Apache Kafka*: Industry standard, but JVM-based, heavy resource footprint ($\ge 3\text{ GB}$ RAM with ZooKeeper/KRaft), slow startup, and high idle CPU consumption.
  - *RabbitMQ*: Excellent AMQP broker, but lacks native partitioned replayable log architecture required for distributed streaming and offset management.
- **Rationale**: Redpanda is written in C++, requires no JVM or ZooKeeper, provides 100% Kafka API compatibility, boots in milliseconds, and operates efficiently within strict memory limits.
- **Governance Rule**: Redpanda is isolated to the `streaming` profile (Phase 4). Static CSV files will **never** be piped over Kafka topics.
- **Hardware Overhead & Cost**: Single container capped at $1.5\text{ GB}$ RAM. Open source (BSL/Apache 2.0).

---

### TDR-08: Data Transformation & Feature Store — Pandas + Columnar Parquet
- **Requirement**: Clean, transform, and calculate rolling statistical features (returns, volatility, volume z-scores) across historical market datasets, storing immutable snapshots for model training.
- **Selected Technology**: **Pandas & Polars + Apache Parquet (Snappy Compressed)**.
- **Alternatives Considered**:
  - *Running Apache Spark for all transformations*: For historical datasets under 10 GB, Spark adds massive JVM overhead, complex cluster coordination, and slower execution than vectorized Python libraries.
  - *Plain CSV / SQLite*: CSV lacks columnar compression, type enforcement, and fast scan speeds; SQLite lacks native columnar analytical performance.
- **Rationale**: Pandas and Polars provide vectorized, CPU-efficient in-memory transformations. Parquet provides schema preservation, 5x–10x storage compression, and columnar partition pruning for fast backtesting.
- **Hardware Overhead & Cost**: Minimal in-memory footprint; zero server daemon required. Open source.

---

### TDR-09: Distributed Stream Processing — Apache Spark (Targeted/Lightweight)
- **Requirement**: Demonstrate distributed stream processing, windowed aggregations, and stream-to-storage persistence for high-velocity financial event feeds.
- **Selected Technology**: **Apache Spark (Structured Streaming, Single-Node Deployment)**.
- **Alternatives Considered**:
  - *Apache Flink*: Outstanding stream processing, but introduces another complex JVM framework and deployment architecture.
- **Rationale**: Spark is a core requirement of postgraduate data engineering curricula and enterprise surveillance architectures. To respect the 16 GB host, Spark is deployed as a single-node worker capped at $2.0\text{ GB}$ memory and executed only during Phase 4 streaming demonstrations.
- **Hardware Overhead & Cost**: $2.0\text{ GB}$ container memory limit; active only under the `streaming` profile. Open source (Apache 2.0).

---

### TDR-10: ML & Volatility Modeling — Scikit-learn, Statsmodels & Arch
- **Requirement**: Implement statistical anomaly baselines (Z-scores, rolling percentiles), unsupervised ML anomaly detection (Isolation Forest), and econometric volatility modeling (EWMA, GARCH).
- **Selected Technology**: **Scikit-learn, Statsmodels, and `arch` library**.
- **Alternatives Considered**:
  - *Deep Learning (LSTM / Transformers / Autoencoders via PyTorch/TensorFlow)*: Deep learning models require significant compute, risk overfitting on non-stationary financial time series, act as unexplainable black boxes to compliance officers, and perform poorly on CPU-only hosts without GPUs.
- **Rationale**: Statistical baselines and Isolation Forest provide explainable, computationally lightweight anomaly detection. Statsmodels and `arch` provide mathematically rigorous implementations of GARCH(1,1) volatility dynamics without requiring GPU acceleration.
- **Hardware Overhead & Cost**: CPU-native execution; minimal memory overhead ($\approx 100-200\text{ MB}$). Open source (BSD).

---

### TDR-11: Experiment Tracking & Model Registry — MLflow
- **Requirement**: Log hyperparameters, training metrics (RMSE, precision@K, alert burden), serialized model binaries, and maintain an immutable lineage of production-deployed anomaly and volatility models.
- **Selected Technology**: **MLflow Tracking & Model Registry**.
- **Alternatives Considered**:
  - *Weights & Biases / Neptune.ai*: Excellent SaaS solutions, but rely on third-party commercial cloud hosting, proprietary APIs, and external credential management.
- **Rationale**: MLflow is fully open-source, local-first, logs model artifacts directly to local disk/PostgreSQL, and integrates seamlessly with Scikit-learn and Python.
- **Hardware Overhead & Cost**: Negligible local footprint; uses existing PostgreSQL backend. Open source (Apache 2.0).

---

### TDR-12: System Observability & Drift Auditing — Prometheus + Grafana + Evidently AI
- **Requirement**: Monitor API throughput/latency, container resource consumption, ingestion pipeline health, and detect feature distribution drift and model prediction degradation over time.
- **Selected Technology**: **Prometheus + Grafana + Evidently AI + Alertmanager**.
- **Alternatives Considered**:
  - *Datadog / New Relic*: Expensive SaaS platforms with recurring subscription costs and proprietary agent overhead.
  - *ELK Stack (Elasticsearch, Logstash, Kibana)*: Elasticsearch requires $\ge 4\text{ GB}$ RAM alone, creating severe memory contention on a 16 GB machine.
- **Rationale**: Prometheus and Grafana provide the gold standard for lightweight time-series metrics collection and visualization ($< 1\text{ GB}$ combined footprint). Evidently AI computes data drift (Wasserstein distance, KS-tests) on tabular feature distributions without requiring active GPU or cloud resources.
- **Hardware Overhead & Cost**: Combined monitoring profile capped at $< 1.5\text{ GB}$ RAM. Open source (Apache 2.0).

---

### TDR-13: LLM Provider Decoupling & Grounded RAG — Decoupled Interface (Groq API Baseline)
- **Requirement**: Generate human-readable, grounded surveillance investigation dossiers with clickable citations, strict zero-hallucination guardrails, and no proprietary vendor lock-in.
- **Selected Technology**: **Abstract `LLMProviderInterface` with Groq Cloud API adapter (Llama-3-70B/8B inference)**.
- **Alternatives Considered**:
  - *Local 7B+ LLM hosting (Ollama / vLLM)*: Running a 7B parameter model locally on a CPU-only machine with 16 GB shared system memory causes extreme token generation latency ($> 30\text{ seconds/request}$) and crashes adjacent Docker services due to RAM exhaustion.
  - *Direct OpenAI / Groq SDK hardcoding*: Direct vendor coupling creates brittle code that breaks when switching providers or API versions.
- **Rationale**: Decoupling the LLM behind an abstract interface (`generate`, `generate_structured`, `health_check`) guarantees zero business logic changes if migrating between Groq, OpenAI, or Gemini. Groq's LPU architecture delivers ultra-low inference latency ($< 1\text{ second}$ generation) on generous free-tier limits.
- **Hardware Overhead & Cost**: Zero local GPU/RAM inference overhead. Free-tier Groq API developer account.

---

### TDR-14: Deployment & Orchestration — Docker Compose Profiles + Minikube
- **Requirement**: Reproducible local multi-service container orchestration with strict resource boundaries, complemented by a local Kubernetes demonstration.
- **Selected Technology**: **Docker Compose (with Profiles) + Minikube (Targeted K8s Manifests)**.
- **Alternatives Considered**:
  - *Full Kubernetes on Docker Desktop / Kind*: Running the entire multi-service stack inside Kubernetes continuously exhausts CPU and memory on a 16 GB laptop.
- **Rationale**: Docker Compose profiles (`core`, `data`, `streaming`, `monitoring`) give the developer exact control over system resources. Minikube is used to demonstrate declarative K8s manifests (Deployments, Services, ConfigMaps, Secrets, Probes) during Phase 12 without permanently bogging down the host machine.
- **Hardware Overhead & Cost**: Configurable and bounded; zero licensing cost. Open source.

---

## 3. Technology Stack Alignment Matrix

| Layer | Selected Tech | Master Prompt Alignment | Hardware Budget (RAM) | Cost Tier |
|---|---|---|---|---|
| **Frontend** | React + TypeScript + Tailwind | Section 5 (Approved Baseline) | 0 MB (Client Browser) | Free / Open Source |
| **Backend** | FastAPI (Python 3.10+) | Section 5 (Approved Baseline) | $\le 1.5\text{ GB}$ | Free / Open Source |
| **Primary Database** | PostgreSQL 16+ | Section 5 (Approved Baseline) | $\le 2.0\text{ GB}$ | Free / Open Source |
| **Vector Search** | `pgvector` Extension | Section 5.1 & Section 9.4 | Shared with PostgreSQL | Free / Open Source |
| **Caching** | Redis 7.x | Section 5.1 & Section 9.10 | $\le 512\text{ MB}$ | Free / Open Source |
| **Batch Orchestration** | Apache Airflow 2.x | Section 5 (Approved Baseline) | $\le 2.0\text{ GB}$ (Profile `data`) | Free / Open Source |
| **Event Streaming** | Redpanda (Single-Broker) | Section 5.1 & Section 4.2 | $\le 1.5\text{ GB}$ (Profile `streaming`) | Free / Open Source |
| **Data Processing** | Pandas / Polars + Parquet | Section 5.1 & Section 3.4 | In-process memory | Free / Open Source |
| **Distributed Streaming** | Apache Spark (Targeted) | Section 5.1 & Section 4.5 | $\le 2.0\text{ GB}$ (Profile `streaming`) | Free / Open Source |
| **ML & Statistics** | Scikit-learn + Statsmodels + Arch | Section 5 & Section 6 | In-process memory | Free / Open Source |
| **Model Tracking** | MLflow | Section 5 & Section 6.6 | $\le 256\text{ MB}$ | Free / Open Source |
| **Observability** | Prometheus + Grafana + Evidently | Section 5 & Section 11 | $\le 1.5\text{ GB}$ (Profile `monitoring`) | Free / Open Source |
| **LLM Provider** | Decoupled Interface (Groq) | Section 6 (LLM Abstraction) | 0 MB local (API) | Free Tier API |
| **Deployment** | Docker Compose + Minikube | Section 5 & Section 12 | Profile bounded ($\le 6\text{ GB}$ active) | Free / Open Source |
