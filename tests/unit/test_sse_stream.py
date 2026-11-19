"""
Unit tests for Real-time SSE Alert Streaming (Phase 10 — Step 10.4).
Verifies authentication guard and SSE streaming delivery.
"""

import json
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_sse_alert_stream_unauthenticated(client):
    """Verify unauthenticated stream access is denied (401)."""
    response = client.get("/api/v1/stream/alerts?limit=2")
    assert response.status_code == 401


def test_sse_alert_stream_endpoint(client):
    # Obtain token
    login_res = client.post("/api/v1/auth/login", json={"username": "analyst1", "password": "analyst_password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Request stream with limit=2 to read exactly 2 events
    response = client.get("/api/v1/stream/alerts?limit=2", headers=headers)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    text = response.text
    assert "event: alert" in text
    assert "data: {" in text
    assert "INFY" in text
    assert "CRITICAL" in text

    # Also test query parameter token (?token=...)
    query_resp = client.get(f"/api/v1/stream/alerts?limit=1&token={token}")
    assert query_resp.status_code == 200
    assert "event: alert" in query_resp.text
