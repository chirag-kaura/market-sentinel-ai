"""
Verification test for Hardened Production Dockerfiles and Security Configurations.
Phase 12 — Step 12.1.
"""

from pathlib import Path


def test_backend_dockerfile_hardening():
    backend_df = Path("deployment/docker/backend.Dockerfile")
    assert backend_df.exists()
    content = backend_df.read_text(encoding="utf-8")

    # Multi-stage check
    assert "AS builder" in content
    assert "AS runtime" in content

    # Non-root user check
    assert "useradd" in content
    assert "USER sentinel" in content

    # Healthcheck check
    assert "HEALTHCHECK" in content
    assert "http://localhost:8000/health" in content


def test_frontend_dockerfile_hardening():
    frontend_df = Path("deployment/docker/frontend.Dockerfile")
    assert frontend_df.exists()
    content = frontend_df.read_text(encoding="utf-8")

    # Multi-stage check
    assert "AS builder" in content
    assert "AS runtime" in content

    # NGINX healthcheck
    assert "HEALTHCHECK" in content
    assert "healthz" in content


def test_nginx_security_headers_and_buffering():
    nginx_conf = Path("deployment/docker/nginx.conf")
    assert nginx_conf.exists()
    content = nginx_conf.read_text(encoding="utf-8")

    # Check headers
    assert "X-Frame-Options \"DENY\"" in content
    assert "X-Content-Type-Options \"nosniff\"" in content

    # SSE buffering bypass
    assert "proxy_buffering off;" in content
    assert "/api/v1/stream/" in content


def test_dockerignore_rules():
    dockerignore = Path(".dockerignore")
    assert dockerignore.exists()
    content = dockerignore.read_text(encoding="utf-8")

    assert ".env" in content
    assert "node_modules/" in content
    assert ".git/" in content
