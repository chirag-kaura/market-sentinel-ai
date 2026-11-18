"""
Verification test for Alertmanager Configuration and Prometheus Alert Rules.
Phase 11 — Step 11.5.
"""

from pathlib import Path
import yaml


def test_alertmanager_config_structure():
    config_file = Path("deployment/alertmanager/alertmanager.yml")
    assert config_file.exists()
    
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
        
    assert "route" in config
    assert "receivers" in config
    assert config["route"]["receiver"] == "surveillance-ops-webhook"
    
    receiver_names = [r["name"] for r in config["receivers"]]
    assert "surveillance-ops-webhook" in receiver_names
    assert "surveillance-critical-pager" in receiver_names


def test_prometheus_alert_rules():
    rules_file = Path("deployment/alertmanager/surveillance_alert_rules.yml")
    assert rules_file.exists()
    
    with open(rules_file, "r") as f:
        rules_data = yaml.safe_load(f)
        
    assert "groups" in rules_data
    sentinel_group = rules_data["groups"][0]
    assert sentinel_group["name"] == "sentinel_surveillance_rules"
    
    alert_names = [r["alert"] for r in sentinel_group["rules"]]
    assert "HighSurveillanceAlertRate" in alert_names
    assert "APIHighLatencyWarning" in alert_names
    assert "HighAPIErrorRate" in alert_names
