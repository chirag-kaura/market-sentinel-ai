"""
Unit Tests for MLflow Experiment Tracking & Model Lineage
Market Sentinel AI — Phase 6: Step 6.6
"""

from pathlib import Path
import json
import pytest

from models.tracking.mlflow_tracker import SurveillanceModelTracker
from models.validation.walk_forward import FoldMetrics


@pytest.fixture
def temp_tracker(tmp_path):
    tracking_dir = tmp_path / "mlflow_test"
    return SurveillanceModelTracker(
        tracking_dir=str(tracking_dir),
        experiment_name="test-surveillance-experiment",
    )


def test_tracker_initialization(temp_tracker):
    assert temp_tracker.experiment_name == "test-surveillance-experiment"
    assert temp_tracker.experiment_dir.exists()


def test_log_training_run_metadata(temp_tracker):
    params = {
        "n_estimators": 100,
        "contamination": 0.02,
        "rolling_window": 20,
    }
    metrics = {
        "train_anomaly_rate": 0.021,
        "mean_iforest_score": 0.245,
    }
    tags = {
        "model_architecture": "IsolationForest",
        "author": "Antigravity",
    }

    dummy_model_artifact = {"weights": [0.1, 0.2, 0.3]}

    run_id = temp_tracker.log_training_run(
        model_name="IsolationForestAnomalyDetector",
        params=params,
        metrics=metrics,
        tags=tags,
        model_artifact=dummy_model_artifact,
    )

    assert run_id.startswith("run_isolationforestanomalydetector_")

    # Read back metadata
    meta = temp_tracker.get_run_metadata(run_id)
    assert meta is not None
    assert meta["run_id"] == run_id
    assert meta["model_name"] == "IsolationForestAnomalyDetector"
    assert meta["params"]["contamination"] == 0.02
    assert meta["metrics"]["train_anomaly_rate"] == 0.021
    assert meta["tags"]["model_architecture"] == "IsolationForest"

    # Verify model artifact was persisted
    art_file = temp_tracker.experiment_dir / run_id / "model.pkl"
    assert art_file.exists()


def test_log_walk_forward_evaluation(temp_tracker):
    fold_metrics = [
        FoldMetrics(
            fold_idx=1,
            train_start="2026-01-01",
            train_end="2026-01-30",
            test_start="2026-02-02",
            test_end="2026-02-15",
            train_rows=60,
            test_rows=30,
            test_anomaly_rate=0.033,
            mean_anomaly_score=0.25,
        ),
        FoldMetrics(
            fold_idx=2,
            train_start="2026-01-01",
            train_end="2026-02-15",
            test_start="2026-02-18",
            test_end="2026-03-01",
            train_rows=90,
            test_rows=30,
            test_anomaly_rate=0.028,
            mean_anomaly_score=0.24,
        ),
    ]

    params = {"contamination": 0.03}
    run_id = temp_tracker.log_walk_forward_evaluation(
        model_name="WalkForward_IsolationForest",
        fold_metrics=fold_metrics,
        params=params,
    )

    meta = temp_tracker.get_run_metadata(run_id)
    assert meta is not None
    assert meta["metrics"]["cv_folds_count"] == 2
    assert meta["metrics"]["cv_total_test_evaluated_rows"] == 60
    assert abs(meta["metrics"]["cv_avg_test_anomaly_rate"] - 0.0305) < 1e-4

    # Verify fold breakdown file exists
    fold_file = temp_tracker.experiment_dir / run_id / "fold_breakdown.json"
    assert fold_file.exists()
    with open(fold_file, "r", encoding="utf-8") as f:
        breakdown = json.load(f)
    assert len(breakdown) == 2
    assert breakdown[0]["fold_idx"] == 1
