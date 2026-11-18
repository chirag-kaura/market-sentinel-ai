"""
Verification test for Grafana Surveillance Dashboard models.
Phase 11 — Step 11.3.
"""

import json
from pathlib import Path


def test_grafana_dashboard_json_structure():
    dashboard_file = Path("deployment/grafana/dashboards/surveillance_command_center.json")
    assert dashboard_file.exists()
    
    with open(dashboard_file, "r") as f:
        data = json.load(f)
        
    assert data["uid"] == "sentinel-command-center"
    assert data["style"] == "dark"
    assert len(data["panels"]) >= 4
    
    # Check key PromQL metrics referenced in panels
    metrics_found = []
    for panel in data["panels"]:
        for target in panel.get("targets", []):
            metrics_found.append(target.get("expr", ""))
            
    all_exprs = " ".join(metrics_found)
    assert "sentinel_surveillance_alerts_total" in all_exprs
    assert "sentinel_http_request_duration_seconds" in all_exprs
    assert "sentinel_active_analyst_sessions" in all_exprs
    assert "sentinel_rag_dossier_generation_seconds" in all_exprs


def test_grafana_provisioning_config():
    config_file = Path("deployment/grafana/provisioning/dashboards.yaml")
    assert config_file.exists()
    content = config_file.read_text(encoding="utf-8")
    assert "MarketSentinelDashboards" in content
