"""
Unit tests for Security, JWT Authentication, and RBAC (Phase 10 — Step 10.5).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.core.security import hash_password, verify_password


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_password_hashing():
    pwd = "secret_password"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed)
    assert not verify_password("wrong_password", hashed)


def test_login_success(client):
    res = client.post("/api/v1/auth/login", json={"username": "analyst1", "password": "analyst_password123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["username"] == "analyst1"
    assert "ANALYST" in data["roles"]


def test_login_invalid_credentials(client):
    res = client.post("/api/v1/auth/login", json={"username": "analyst1", "password": "wrong_password"})
    assert res.status_code == 401
    assert res.json()["error_code"] == "INVALID_CREDENTIALS"


def test_protected_profile_endpoint(client):
    # Missing token -> 401
    res_unauth = client.get("/api/v1/auth/me")
    assert res_unauth.status_code == 401
    assert res_unauth.json()["error_code"] == "MISSING_TOKEN"

    # Login and get token
    login_res = client.post("/api/v1/auth/login", json={"username": "analyst1", "password": "analyst_password123"})
    token = login_res.json()["access_token"]

    # Authenticated call
    headers = {"Authorization": f"Bearer {token}"}
    res_auth = client.get("/api/v1/auth/me", headers=headers)
    assert res_auth.status_code == 200
    assert res_auth.json()["username"] == "analyst1"


def test_rbac_admin_guard(client):
    # Login as analyst
    analyst_token = client.post(
        "/api/v1/auth/login", json={"username": "analyst1", "password": "analyst_password123"}
    ).json()["access_token"]

    # Analyst tries to access admin route -> 403 Forbidden
    res_forbidden = client.get("/api/v1/auth/admin/audit", headers={"Authorization": f"Bearer {analyst_token}"})
    assert res_forbidden.status_code == 403
    assert res_forbidden.json()["error_code"] == "FORBIDDEN_INSUFFICIENT_PERMISSIONS"

    # Login as admin
    admin_token = client.post(
        "/api/v1/auth/login", json={"username": "admin1", "password": "admin_password123"}
    ).json()["access_token"]

    # Admin accesses admin route -> 200 OK
    res_admin = client.get("/api/v1/auth/admin/audit", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    assert res_admin.json()["status"] == "ok"
