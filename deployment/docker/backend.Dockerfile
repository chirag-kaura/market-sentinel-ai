# syntax=docker/dockerfile:1
# Multi-stage Hardened Production Dockerfile for Market Sentinel AI Backend

# Stage 1: Build & Dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY deployment/docker/requirements-docker.txt ./requirements-docker.txt
RUN pip install --no-cache-dir --user -r requirements-docker.txt

# Stage 2: Minimal Distroless / Hardened Runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

# Create non-root system user and group
RUN groupadd -g 10001 sentinel && \
    useradd -u 10001 -g sentinel -s /bin/bash -m sentinel

# Copy installed Python packages from builder
COPY --from=builder /root/.local /home/sentinel/.local

# Ensure path includes user installed binaries
ENV PATH=/home/sentinel/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy application source code
COPY --chown=sentinel:sentinel backend ./backend
COPY --chown=sentinel:sentinel data ./data
COPY --chown=sentinel:sentinel ingestion ./ingestion
COPY --chown=sentinel:sentinel intelligence ./intelligence
COPY --chown=sentinel:sentinel models ./models
COPY --chown=sentinel:sentinel monitoring ./monitoring
COPY --chown=sentinel:sentinel processing ./processing
COPY --chown=sentinel:sentinel scripts ./scripts
COPY --chown=sentinel:sentinel streaming ./streaming

USER sentinel

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
