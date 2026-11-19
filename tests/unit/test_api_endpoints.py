"""
Unit tests for Core RESTful API Endpoints (Phase 10 — Step 10.3 / 10.5).
Verifies authentication enforcement, alert retrieval, persistent case management,
and regulatory audit dispositions.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Authenticate as standard analyst."""
    res = client.post("/api/v1/auth/login", json={"username": "analyst1", "password": "analyst_password123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def officer_headers(client):
    """Authenticate as senior compliance officer."""
    res = client.post("/api/v1/auth/login", json={"username": "officer1", "password": "officer_password123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_unauthenticated_endpoints_require_token(client):
    """Verify surveillance endpoints block unauthenticated access (401)."""
    assert client.get("/api/v1/alerts").status_code == 401
    assert client.get("/api/v1/investigations").status_code == 401
    assert client.get("/api/v1/stream/alerts").status_code == 401


def test_list_alerts_endpoint(client, auth_headers):
    response = client.get("/api/v1/alerts", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "alert_id" in data[0]
    assert "composite_risk_score" in data[0]


def test_list_alerts_with_filters(client, auth_headers):
    response = client.get("/api/v1/alerts?ticker=INFY&priority=CRITICAL", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["ticker"] == "INFY"
    assert data[0]["priority_level"] == "CRITICAL"


def test_get_alert_detail_success(client, auth_headers):
    response = client.get("/api/v1/alerts/ALT-202611-001", headers=auth_headers)
    assert response.status_code == 200
    detail = response.json()
    assert detail["alert_id"] == "ALT-202611-001"
    assert detail["abnormal_return"] == 0.048
    assert len(detail["citations"]) >= 1


def test_get_alert_detail_not_found(client, auth_headers):
    response = client.get("/api/v1/alerts/NON-EXISTENT-ALERT", headers=auth_headers)
    assert response.status_code == 404
    error_data = response.json()
    assert error_data["error_code"] == "ENTITY_NOT_FOUND"


def test_list_symbols_and_get_symbol(client):
    # Public market symbol metadata
    list_res = client.get("/api/v1/market/symbols")
    assert list_res.status_code == 200
    symbols = list_res.json()
    assert len(symbols) >= 2

    detail_res = client.get("/api/v1/market/symbols/INFY")
    assert detail_res.status_code == 200
    assert detail_res.json()["symbol"] == "INFY"

    missing_res = client.get("/api/v1/market/symbols/UNKNOWN")
    assert missing_res.status_code == 404


def test_investigations_crud_and_persistence(client, auth_headers, officer_headers):
    # 1. List cases
    list_res = client.get("/api/v1/investigations", headers=auth_headers)
    assert list_res.status_code == 200
    cases = list_res.json()
    assert len(cases) >= 1

    # 2. Get case detail
    case_id = cases[0]["case_id"]
    detail_res = client.get(f"/api/v1/investigations/{case_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["case_id"] == case_id

    # 3. Add analyst notes
    notes_payload = {"notes": "Verified broker clearing data for high-volume transactions."}
    notes_res = client.post(f"/api/v1/investigations/{case_id}/notes", json=notes_payload, headers=auth_headers)
    assert notes_res.status_code == 200
    assert "broker clearing data" in notes_res.json()["analyst_notes"]

    # 4. Status update
    status_payload = {"status": "UNDER_REVIEW", "rationale": "Cross-verifying with corporate filing"}
    status_res = client.patch(f"/api/v1/investigations/{case_id}/status", json=status_payload, headers=auth_headers)
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "UNDER_REVIEW"

    # 5. Analyst cannot escalate to SAR (requires Compliance Officer / Admin)
    esc_payload = {"rationale": "Suspicious insider order cluster before public earnings"}
    esc_fail_res = client.post(f"/api/v1/investigations/{case_id}/escalate", json=esc_payload, headers=auth_headers)
    assert esc_fail_res.status_code == 403

    # 6. Compliance Officer escalates to SAR
    esc_ok_res = client.post(f"/api/v1/investigations/{case_id}/escalate", json=esc_payload, headers=officer_headers)
    assert esc_ok_res.status_code == 200
    assert esc_ok_res.json()["status"] == "ESCALATED_SAR"

    # 7. Check immutable audit trail
    audit_res = client.get("/api/v1/investigations/audit/dispositions", headers=auth_headers)
    assert audit_res.status_code == 200
    audit_logs = audit_res.json()
    assert len(audit_logs) >= 2
    actions = [log["action"] for log in audit_logs]
    assert "NOTE_ADDED" in actions
    assert "STATUS_ESCALATED_SAR" in actions
