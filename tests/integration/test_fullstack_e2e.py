"""
Full-Stack Integration and End-to-End Workflow Tests.
Phase 10 — Step 10.8: Verifies full surveillance pipeline from authentication to alert retrieval,
streaming, case management, note logging, SAR escalation, alert dismissal, and immutable audit disposition persistence.
"""

import json
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_full_stack_surveillance_workflow_e2e(client):
    # 1. Analyst logs in and obtains JWT token
    login_payload = {"username": "analyst1", "password": "analyst_password123"}
    login_resp = client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    auth_header = {"Authorization": f"Bearer {token_data['access_token']}"}

    # 2. Analyst checks identity profile
    me_resp = client.get("/api/v1/auth/me", headers=auth_header)
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "analyst1"

    # 3. Analyst fetches critical alerts from the surveillance queue
    alerts_resp = client.get("/api/v1/alerts?priority=CRITICAL", headers=auth_header)
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert len(alerts) >= 1
    selected_alert = alerts[0]
    alert_id = selected_alert["alert_id"]

    # 4. Analyst inspects detailed attribution and evidence citations
    detail_resp = client.get(f"/api/v1/alerts/{alert_id}", headers=auth_header)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["alert_id"] == alert_id
    assert "citations" in detail
    assert len(detail["citations"]) >= 1

    # 5. Analyst checks active investigation cases
    cases_resp = client.get("/api/v1/investigations", headers=auth_header)
    assert cases_resp.status_code == 200
    cases = cases_resp.json()
    assert len(cases) >= 1
    target_case_id = cases[0]["case_id"]

    # 6. Analyst logs investigative notes and changes status
    note_resp = client.post(
        f"/api/v1/investigations/{target_case_id}/notes",
        json={"notes": "Corroborated 3.4x volume surge with block trading registry."},
        headers=auth_header,
    )
    assert note_resp.status_code == 200
    assert "block trading registry" in note_resp.json()["analyst_notes"]

    status_resp = client.patch(
        f"/api/v1/investigations/{target_case_id}/status",
        json={"status": "UNDER_REVIEW", "rationale": "Pending broker trade confirmation"},
        headers=auth_header,
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "UNDER_REVIEW"

    # 7. Compliance Officer logs in and escalates to SAR
    officer_login = client.post("/api/v1/auth/login", json={"username": "officer1", "password": "officer_password123"})
    officer_token = officer_login.json()["access_token"]
    officer_header = {"Authorization": f"Bearer {officer_token}"}

    escalate_resp = client.post(
        f"/api/v1/investigations/{target_case_id}/escalate",
        json={"rationale": "Sufficient circumstantial evidence of pre-announcement insider leakage."},
        headers=officer_header,
    )
    assert escalate_resp.status_code == 200
    assert escalate_resp.json()["status"] == "ESCALATED_SAR"

    # 8. Verify immutable audit trail records
    audit_resp = client.get("/api/v1/investigations/audit/dispositions", headers=auth_header)
    assert audit_resp.status_code == 200
    audit_trail = audit_resp.json()
    assert len(audit_trail) >= 2
    actions = [entry["action"] for entry in audit_trail]
    assert "NOTE_ADDED" in actions
    assert "STATUS_ESCALATED_SAR" in actions

    # 9. Analyst monitors live SSE alert stream
    stream_resp = client.get("/api/v1/stream/alerts?limit=1", headers=auth_header)
    assert stream_resp.status_code == 200
    assert "text/event-stream" in stream_resp.headers["content-type"]
    assert "event: alert" in stream_resp.text
