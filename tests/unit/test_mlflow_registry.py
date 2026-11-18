"""
Unit tests for Continuous MLflow Production Registry (Phase 11 — Step 11.7).
"""

import os
import pytest
from models.registry.registry_manager import MLflowProductionRegistry


@pytest.fixture
def temp_registry_path(tmp_path):
    return str(tmp_path / "test_model_catalog.json")


def test_register_model_version(temp_registry_path):
    reg = MLflowProductionRegistry(registry_path=temp_registry_path)
    meta = reg.register_model_version(
        model_name="isolation_forest_volume",
        version="1.0.0",
        hyperparameters={"n_estimators": 100.0, "contamination": 0.05},
        metrics={"auc_pr": 0.88, "precision": 0.85},
        artifact_uri="s3://sentinel-models/iforest_v1.pkl",
    )
    assert meta.model_name == "isolation_forest_volume"
    assert meta.stage == "STAGING"
    assert meta.metrics["auc_pr"] == 0.88


def test_transition_stage_and_active_production(temp_registry_path):
    reg = MLflowProductionRegistry(registry_path=temp_registry_path)
    
    # Register v1.0.0 and promote to PRODUCTION
    reg.register_model_version(
        model_name="garch_volatility",
        version="1.0.0",
        hyperparameters={"p": 1.0, "q": 1.0},
        metrics={"aic": 1420.5},
        artifact_uri="s3://models/garch_v1.pkl",
    )
    reg.transition_stage("garch_volatility", "1.0.0", "PRODUCTION")
    
    active_prod = reg.get_production_model("garch_volatility")
    assert active_prod is not None
    assert active_prod.version == "1.0.0"

    # Register v1.1.0 and promote; v1.0.0 should automatically demote to ARCHIVED
    reg.register_model_version(
        model_name="garch_volatility",
        version="1.1.0",
        hyperparameters={"p": 1.0, "q": 1.0},
        metrics={"aic": 1390.2},
        artifact_uri="s3://models/garch_v2.pkl",
    )
    reg.transition_stage("garch_volatility", "1.1.0", "PRODUCTION")

    new_prod = reg.get_production_model("garch_volatility")
    assert new_prod.version == "1.1.0"
    
    # Reload from disk to verify persistence
    reloaded_reg = MLflowProductionRegistry(registry_path=temp_registry_path)
    assert reloaded_reg.get_production_model("garch_volatility").version == "1.1.0"
