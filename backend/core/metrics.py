"""
Prometheus Metrics Instrumentation for Market Sentinel AI.
Phase 11 — Step 11.2: Defines system, surveillance, and RAG telemetry counters and histograms.
"""

import time
from typing import Callable
from fastapi import Request, Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY,
)
from starlette.middleware.base import BaseHTTPMiddleware

# Surveillance Business Metrics
SURVEILLANCE_ALERTS_TOTAL = Counter(
    "sentinel_surveillance_alerts_total",
    "Total count of surveillance alerts generated",
    ["ticker", "priority", "anomaly_category"],
)

RAG_DOSSIER_GENERATION_LATENCY = Histogram(
    "sentinel_rag_dossier_generation_seconds",
    "Time taken to generate grounded investigation dossier",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

ACTIVE_ANALYST_SESSIONS = Gauge(
    "sentinel_active_analyst_sessions",
    "Number of active logged-in surveillance analysts",
)

# HTTP Request Metrics
HTTP_REQUESTS_TOTAL = Counter(
    "sentinel_http_requests_total",
    "Total HTTP requests received",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "sentinel_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """ASGI middleware measuring request duration and counting status codes."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        endpoint = request.url.path

        try:
            response: Response = await call_next(request)
            duration = time.perf_counter() - start_time
            status_code = str(response.status_code)

            HTTP_REQUESTS_TOTAL.labels(
                method=request.method, endpoint=endpoint, status_code=status_code
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method, endpoint=endpoint
            ).observe(duration)

            return response
        except Exception:
            duration = time.perf_counter() - start_time
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method, endpoint=endpoint, status_code="500"
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method, endpoint=endpoint
            ).observe(duration)
            raise


def record_feature_drift(symbol: str, feature: str, psi_score: float) -> None:
    """Updates the Prometheus Gauge for a feature's Population Stability Index (PSI)."""
    FEATURE_DRIFT_PSI.labels(symbol=symbol, feature=feature).set(psi_score)


FEATURE_DRIFT_PSI = Gauge(
    "sentinel_feature_psi",
    "Population Stability Index (PSI) drift score per symbol and feature",
    ["symbol", "feature"],
)


def get_prometheus_metrics_payload() -> bytes:
    """Renders Prometheus registry scrape output in standard text exposition format."""
    return generate_latest(REGISTRY)
