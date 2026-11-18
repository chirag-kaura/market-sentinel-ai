"""
Verification test for React Surveillance Dashboard Components.
Phase 10 — Step 10.7.
"""

from pathlib import Path


def test_components_exist():
    comp_dir = Path("frontend/src/components")
    assert (comp_dir / "AlertQueue.tsx").exists()
    assert (comp_dir / "DossierViewer.tsx").exists()
    assert Path("frontend/src/App.tsx").exists()


def test_alert_queue_component_contract():
    content = Path("frontend/src/components/AlertQueue.tsx").read_text(encoding="utf-8")
    assert "Surveillance Alert Queue" in content
    assert "onSelectAlert" in content
    assert "composite_risk_score" in content


def test_dossier_viewer_component_contract():
    content = Path("frontend/src/components/DossierViewer.tsx").read_text(encoding="utf-8")
    assert "Surveillance Feature Attribution" in content
    assert "Abnormal Return" in content
    assert "Evidence Citations" in content
    assert "Zero-Hallucination Policy Enforced" in content


def test_app_main_workspace_integration():
    content = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    assert "MARKET SENTINEL" in content
    assert "subscribeToAlertStream" in content
    assert "AlertQueue" in content
    assert "DossierViewer" in content
