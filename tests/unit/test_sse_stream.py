"""
Unit tests for Real-time SSE Alert Streaming (Phase 10 — Step 10.4).
"""

import json
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_sse_alert_stream_endpoint(client):
    # Request stream with limit=2 to read exactly 2 events
    response = client.get("/api/v1/stream/alerts?limit=2")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    
    text = response.text
    assert "event: alert" in text
    assert "data: {" in text
    assert "INFY" in text
    assert "CRITICAL" in text
