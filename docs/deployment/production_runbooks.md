# Market Sentinel AI — Production Runbooks & Operations Manual

## 1. System Architecture Overview
Market Sentinel AI is an AI-powered stock market surveillance and risk intelligence decision-support platform designed to operate on a constrained local development environment (Windows 11, 16 GB RAM, CPU-only, Docker Desktop with WSL 2) while scaling to cloud-native Kubernetes environments.

---

## 2. Standard Operating Procedures (SOP)

### SOP-01: Cold-Start Deployment via Docker Compose
To boot the platform core tier (PostgreSQL with `pgvector`, Redis, FastAPI, and React NGINX frontend):
```bash
# 1. Inspect environment variables
cp .env.example .env

# 2. Boot core profile (memory-bounded)
docker compose --profile core up -d

# 3. Verify health probes
python scripts/health/health_probes.py
```

### SOP-02: Activating Streaming & Observability Profiles
Never boot streaming and observability concurrently with distributed batch pipelines on 16 GB RAM.
```bash
# Boot streaming (Redpanda single broker)
docker compose --profile streaming up -d

# Boot monitoring stack (Prometheus, Grafana, Alertmanager)
docker compose --profile monitoring up -d
# Access Grafana Dashboard at: http://localhost:3001 (Default credentials: admin / admin)
```

### SOP-03: Model Registry Promotion
To promote a newly evaluated surveillance model candidate to active production:
```python
from models.registry.registry_manager import MLflowProductionRegistry

reg = MLflowProductionRegistry()
# Automatically activates candidate and demotes previous version to ARCHIVED
reg.transition_stage(model_name="isolation_forest_volume", version="1.1.0", new_stage="PRODUCTION")
```

---

## 3. Incident Management & Disaster Recovery Runbooks

### INC-01: High 5xx API Error Rate or Database Dropout
1. **Detection**: Prometheus Alert `HighAPIErrorRate` fires, or Sentry reports connection exceptions.
2. **Investigation**:
   - Inspect structured logs: `docker logs sentinel-backend --tail 100`
   - Filter logs by `X-Correlation-ID` reported in Sentry.
3. **Resolution**:
   - Check PostgreSQL status: `docker exec -it sentinel-postgres pg_isready -U sentinel`
   - If PostgreSQL crashed due to memory limits, restart container: `docker compose restart postgres`

### INC-02: LLM Cloud Gateway Timeout / Rate Limits
1. **Detection**: RAG dossier generation times exceed 10s or `sentinel_rag_dossier_generation_seconds` spikes.
2. **Resolution**:
   - Verify Groq API status.
   - Core FastAPI backend maintains graceful fallback: if external LLM times out, endpoints surface deterministic structured surveillance metrics without crashing.
