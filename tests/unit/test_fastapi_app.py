"""Unit tests for FastAPI Application Factory and Health Probes (Phase 10 — Step 10.1)."""
from fastapi.testclient import TestClient
import pytest
from backend.main import create_app
from backend.core.exceptions import EntityNotFoundError, SurveillanceValidationError


@pytest.fixture
def client():
    app = create_app()

    # Register temporary test routes to verify custom exception handling
    @app.get("/test/not-found")
    async def trigger_not_found():
        raise EntityNotFoundError(entity_name="Symbol", entity_id="INVALID_XYZ")

    @app.get("/test/validation-error")
    async def trigger_val_error():
        raise SurveillanceValidationError(message="Invalid temporal parameter lookback_days.")

    @app.get("/test/unhandled-error")
    async def trigger_unhandled():
        raise RuntimeError("Unexpected simulated failure.")

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "market-sentinel-api"
    assert "timestamp" in data


def test_readiness_probe_endpoint(client):
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_custom_entity_not_found_exception(client):
    response = client.get("/test/not-found")
    assert response.status_code == 404
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "ENTITY_NOT_FOUND"
    assert "INVALID_XYZ" in data["message"]


def test_custom_validation_exception(client):
    response = client.get("/test/validation-error")
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "VALIDATION_ERROR"


def test_unhandled_exception_returns_500_without_stack_leak(client):
    response = client.get("/test/unhandled-error")
    assert response.status_code == 500
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "INTERNAL_SERVER_ERROR"
    # Ensure raw Python traceback is hidden
    assert "Traceback" not in response.text
