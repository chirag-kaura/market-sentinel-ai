"""
Unit tests for Core RESTful API Endpoints (Phase 10 — Step 10.3).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_list_alerts_endpoint(client):
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "alert_id" in data[0]
    assert "composite_risk_score" in data[0]


def test_list_alerts_with_filters(client):
    response = client.get("/api/v1/alerts?ticker=INFY&priority=CRITICAL")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["ticker"] == "INFY"
    assert data[0]["priority_level"] == "CRITICAL"


def test_get_alert_detail_success(client):
    response = client.get("/api/v1/alerts/ALT-202611-001")
    assert response.status_code == 200
    detail = response.json()
    assert detail["alert_id"] == "ALT-202611-001"
    assert detail["abnormal_return"] == 0.048
    assert len(detail["citations"]) >= 1


def test_get_alert_detail_not_found(client):
    response = client.get("/api/v1/alerts/NON-EXISTENT-ALERT")
    assert response.status_code == 404
    error_data = response.json()
    assert error_data["error_code"] == "ENTITY_NOT_FOUND"


def test_list_symbols_and_get_symbol(client):
    # Test list symbols
    list_res = client.get("/api/v1/market/symbols")
    assert list_res.status_code == 200
    symbols = list_res.json()
    assert len(symbols) >= 2
    
    # Test get symbol detail
    detail_res = client.get("/api/v1/market/symbols/INFY")
    assert detail_res.status_code == 200
    assert detail_res.json()["company_name"] == "Infosys Limited"

    # Test not found
    missing_res = client.get("/api/v1/market/symbols/UNKNOWN")
    assert missing_res.status_code == 404


def test_investigations_endpoints(client):
    # Test list cases
    list_cases_res = client.get("/api/v1/investigations")
    assert list_cases_res.status_code == 200
    cases = list_cases_res.json()
    assert len(cases) >= 1
    assert cases[0]["case_id"] == "CASE-2026-001"

    # Test get single case
    case_detail_res = client.get("/api/v1/investigations/CASE-2026-001")
    assert case_detail_res.status_code == 200
    assert case_detail_res.json()["ticker"] == "INFY"
