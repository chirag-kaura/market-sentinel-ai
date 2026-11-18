"""
Verification test for Multi-Profile Docker Compose Configuration.
Phase 12 — Step 12.2.
"""

from pathlib import Path
import yaml


def test_docker_compose_profiles_and_limits():
    compose_file = Path("docker-compose.yml")
    assert compose_file.exists()

    with open(compose_file, "r") as f:
        compose = yaml.safe_load(f)

    assert "services" in compose
    services = compose["services"]

    # Verify key services exist
    assert "postgres" in services
    assert "redis" in services
    assert "backend" in services
    assert "frontend" in services
    assert "redpanda" in services
    assert "prometheus" in services
    assert "grafana" in services
    assert "alertmanager" in services

    # Verify multi-profile segregation
    assert "core" in services["backend"]["profiles"]
    assert "core" in services["frontend"]["profiles"]
    assert "streaming" in services["redpanda"]["profiles"]
    assert "monitoring" in services["prometheus"]["profiles"]

    # Verify mandatory hardware resource limits in every service (AGENTS.md compliance)
    for s_name, s_def in services.items():
        assert "deploy" in s_def, f"Service {s_name} missing deploy configuration"
        assert "resources" in s_def["deploy"], f"Service {s_name} missing resources configuration"
        assert "limits" in s_def["deploy"]["resources"], f"Service {s_name} missing resource limits"
        limits = s_def["deploy"]["resources"]["limits"]
        assert "memory" in limits, f"Service {s_name} missing memory limit"
        assert "cpus" in limits, f"Service {s_name} missing cpus limit"
