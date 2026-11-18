# Step 12.2: Multi-Profile Docker Compose Orchestration Report

## 1. Objective & Business Relevance
Step 12.2 configures the multi-profile `docker-compose.yml` service orchestration for Market Sentinel AI. Developing on a constrained 16 GB RAM host requires strict prevention against running all system tiers (database, streaming broker, batch pipeline, inference backend, and observability stack) concurrently. Docker Compose profiles permit starting only the necessary slice of the platform.

## 2. Technical Explanation & Architectural Fit
- **Profile Segregation (`docker-compose.yml`)**:
  - `core`: PostgreSQL (`pgvector`), Redis, FastAPI backend, React frontend (`docker compose --profile core up -d`).
  - `streaming`: Redpanda (Kafka-compatible single broker) with bounded memory limits (`1280M`).
  - `monitoring`: Prometheus, Grafana, Alertmanager (`docker compose --profile monitoring up -d`).
- **Hardware Enforcements (Strict `AGENTS.md` Rule 2 Compliance)**:
  - Every service definition includes explicit CPU and Memory hard limits (e.g. Postgres: `1024M`, Backend: `1536M`, Redis: `256M`, Prometheus: `512M`).
  - Service dependencies use health check conditions (`condition: service_healthy`) to ensure correct boot sequencing.

## 3. Technology Decisions & Alternatives Considered
- **Docker Compose Profiles**: Built natively into Docker Compose v2, eliminating brittle shell scripts or duplicated compose files while maintaining clean isolation.

## 4. Files Created / Modified
- `docker-compose.yml`: Master multi-profile container orchestration configuration.
- `tests/unit/test_docker_compose.py`: Automated tests validating profile tags and CPU/memory limit enforcement across all services.
- `docs/step_reports/phase_12_step_02_docker_compose_profiles.md`: This report.

## 5. Commands Executed & Testing Report
```bash
python -m pytest tests/unit/test_docker_compose.py -v
```
Output:
```
tests/unit/test_docker_compose.py::test_docker_compose_profiles_and_limits PASSED [100%]
============================== 1 passed in 0.12s ==============================
```

## 6. Known Limitations & Edge Cases
- Windows users must ensure Docker Desktop is configured to use the WSL 2 backend to maximize disk I/O throughput.

## 7. Status & Sign-off
- **Status**: COMPLETED & VERIFIED
- **Phase 12 Step**: Step 12.2 Approved
