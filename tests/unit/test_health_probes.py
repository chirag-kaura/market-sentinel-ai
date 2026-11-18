"""
Unit tests for Service Health Probes and Dependency Management (Phase 12 — Step 12.3).
"""

from unittest.mock import MagicMock
import pytest
from scripts.health.health_probes import (
    probe_http_endpoint,
    wait_for_service,
    run_system_health_audit,
)


def test_probe_http_endpoint_success(monkeypatch):
    class MockResponse:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout: MockResponse())
    healthy, msg = probe_http_endpoint("http://mock-service/health")
    assert healthy
    assert "HTTP 200 OK" in msg


def test_probe_http_endpoint_failure(monkeypatch):
    def mock_failing_urlopen(*args, **kwargs):
        raise ConnectionRefusedError("Connection refused by host.")

    monkeypatch.setattr("urllib.request.urlopen", mock_failing_urlopen)
    healthy, msg = probe_http_endpoint("http://mock-service/health")
    assert not healthy
    assert "Connection failure" in msg


def test_wait_for_service_retry_recovery(monkeypatch):
    call_count = 0

    class MockResponse:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    def flaky_urlopen(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionRefusedError("Service starting up...")
        return MockResponse()

    monkeypatch.setattr("urllib.request.urlopen", flaky_urlopen)
    success = wait_for_service("Backend API", "http://mock-backend/health", max_retries=3, delay_seconds=0.01)
    assert success
    assert call_count == 2


def test_run_system_health_audit(monkeypatch):
    class MockResponse:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout: MockResponse())
    results = run_system_health_audit({
        "Backend": "http://localhost:8000/health",
        "Frontend": "http://localhost/healthz",
    })
    assert results["Backend"] is True
    assert results["Frontend"] is True
