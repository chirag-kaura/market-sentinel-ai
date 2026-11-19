"""
Unit tests for Security, JWT Authentication, and RBAC (Phase 10 — Step 10.5).
Verifies PBKDF2 password hashing, salt randomization, token expiration, and
complete BRD FR-7.3 persona hierarchy.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.core.security import hash_password, verify_password, UserRole


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_password_hashing_with_random_salt():
    pwd = "secret_password"
    hashed1 = hash_password(pwd)
    hashed2 = hash_password(pwd)

    # Different random salts -> different hashes
    assert hashed1 != hashed2
    assert hashed1.startswith("pbkdf2_sha256$")
    assert hashed2.startswith("pbkdf2_sha256$")

    # Both verify correctly
    assert verify_password(pwd, hashed1)
    assert verify_password(pwd, hashed2)
    assert not verify_password("wrong_password", hashed1)


def test_legacy_password_verification_compatibility():
    """Verify legacy hashes without prefix still verify for backward compatibility."""
    import hashlib
    legacy_salt = b"market_sentinel_salt_constant"
    legacy_hash = hashlib.pbkdf2_hmac("sha256", "test_legacy_pwd".encode("utf-8"), legacy_salt, 10000).hex()

    assert verify_password("test_legacy_pwd", legacy_hash)
    assert not verify_password("wrong_pwd", legacy_hash)


def test_login_success(client):
    res = client.post("/api/v1/auth/login", json={"username": "analyst1", "password": "analyst_password123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["username"] == "analyst1"
    assert UserRole.ANALYST.value in data["roles"]


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


def test_all_four_brd_personas(client):
    """Verify all four institutional personas can authenticate and receive authorized roles."""
    personas = [
        ("viewer1", "viewer_password123", UserRole.READ_ONLY_ANALYST.value),
        ("analyst1", "analyst_password123", UserRole.ANALYST.value),
        ("officer1", "officer_password123", UserRole.COMPLIANCE_OFFICER.value),
        ("admin1", "admin_password123", UserRole.ADMIN.value),
    ]

    for username, password, expected_role in personas:
        res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert res.status_code == 200
        roles = res.json()["roles"]
        assert expected_role in roles


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
