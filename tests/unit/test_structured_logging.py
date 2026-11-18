"""
Unit tests for Structured JSON Logging & Correlation ID Middleware (Phase 11 — Step 11.1).
"""

import json
import logging
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.core.logging import JSONFormatter, setup_structured_logging, correlation_id_ctx


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_json_formatter_structure():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=42,
        msg="Surveillance test message",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)
    
    assert data["level"] == "INFO"
    assert data["message"] == "Surveillance test message"
    assert data["logger"] == "test_logger"
    assert "timestamp" in data
    assert "correlation_id" in data


def test_correlation_id_auto_generation(client):
    # Request without explicit X-Correlation-ID should receive generated header
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-correlation-id" in response.headers
    corr_id = response.headers["x-correlation-id"]
    assert len(corr_id) > 10


def test_correlation_id_preservation(client):
    # Request with custom X-Correlation-ID should retain the same value
    custom_id = "AUDIT-TRACE-998877"
    response = client.get("/health", headers={"X-Correlation-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["x-correlation-id"] == custom_id
