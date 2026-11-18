"""
Unit tests for Prometheus Metrics Instrumentation (Phase 11 — Step 11.2).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.core.metrics import (
    SURVEILLANCE_ALERTS_TOTAL,
    RAG_DOSSIER_GENERATION_LATENCY,
    ACTIVE_ANALYST_SESSIONS,
)


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_prometheus_metrics_scrape_endpoint(client):
    # Perform a request to generate traffic
    client.get("/health")
    
    # Scrape metrics endpoint
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    
    content = response.text
    assert "sentinel_http_requests_total" in content
    assert "sentinel_http_request_duration_seconds" in content


def test_surveillance_custom_metrics_increment(client):
    # Record custom domain metric events
    SURVEILLANCE_ALERTS_TOTAL.labels(
        ticker="INFY", priority="CRITICAL", anomaly_category="SURGE"
    ).inc()
    
    RAG_DOSSIER_GENERATION_LATENCY.observe(0.45)
    ACTIVE_ANALYST_SESSIONS.set(3)
    
    # Verify in scrape endpoint
    response = client.get("/metrics")
    text = response.text
    
    assert "sentinel_surveillance_alerts_total" in text
    assert 'ticker="INFY"' in text
    assert "sentinel_rag_dossier_generation_seconds" in text
    assert "sentinel_active_analyst_sessions" in text
