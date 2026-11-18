"""
MLflow Experiment & Model Lineage Tracker (Phase 6 — Step 6.6)
Market Sentinel AI — Model Registry & Experiment Governance

Tracks surveillance model training runs, hyperparameters, walk-forward cross-validation
metrics, feature lineage, and model artifacts using local MLflow file store semantics:
- Tracks Statistical Baseline, Isolation Forest, and EWMA/GARCH models.
- Logs hyperparameter configurations (contamination, n_estimators, lambda, rolling windows).
- Records fold-by-fold out-of-sample walk-forward validation metrics.
- Persists serializable model artifacts locally under data/models/mlflow/.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("market_sentinel.models.tracking.mlflow_tracker")
logger.setLevel(logging.INFO)


class SurveillanceModelTracker:
    """
    Standardized experiment tracker for surveillance model governance.
    Operates over local directory storage (file:./data/models/mlflow) to ensure
    zero external server dependency during local CPU development.
    """

    DEFAULT_TRACKING_DIR = "data/models/mlflow"
    DEFAULT_EXPERIMENT_NAME = "market-sentinel-surveillance-models"

    def __init__(
        self,
        tracking_dir: str = DEFAULT_TRACKING_DIR,
        experiment_name: str = DEFAULT_EXPERIMENT_NAME,
    ):
        self.tracking_dir = Path(tracking_dir)
        self.experiment_name = experiment_name
        self.experiment_dir = self.tracking_dir / self.experiment_name
        self.experiment_dir.mkdir(parents=True, exist_ok=True)
        self._mlflow_available = False

        # Attempt to configure native MLflow if installed
        try:
            import mlflow
            self.mlflow = mlflow
            mlflow.set_tracking_uri(f"file:{self.tracking_dir.resolve().as_posix()}")
            mlflow.set_experiment(self.experiment_name)
            self._mlflow_available = True
            logger.info("Configured native MLflow file store at %s", self.tracking_dir)
        except ImportError:
            logger.info("MLflow package not installed. Utilizing structured JSON file-store tracker.")

    def log_training_run(
        self,
        model_name: str,
        params: Dict[str, Any],
        metrics: Dict[str, float],
        tags: Optional[Dict[str, str]] = None,
        model_artifact: Optional[Any] = None,
    ) -> str:
        """
        Logs a training experiment run, persisting parameters, metrics, tags, and artifacts.
        Returns the unique run_id.
        """
        run_id = f"run_{model_name.lower()}_{uuid.uuid4().hex[:12]}"
        timestamp_utc = datetime.now(timezone.utc).isoformat()
        tags = tags or {}
        tags["model_name"] = model_name
        tags["logged_at_utc"] = timestamp_utc

        # 1. Native MLflow logging if available
        if self._mlflow_available:
            try:
                with self.mlflow.start_run(run_name=f"{model_name}_{run_id}") as active_run:
                    self.mlflow.log_params(params)
                    self.mlflow.log_metrics(metrics)
                    self.mlflow.set_tags(tags)
                    # If model_artifact is provided and has pickle/dump capability
                    if model_artifact is not None:
                        import pickle
                        art_path = self.experiment_dir / f"{run_id}_model.pkl"
                        with open(art_path, "wb") as f:
                            pickle.dump(model_artifact, f)
                        self.mlflow.log_artifact(str(art_path))
                    return active_run.info.run_id
            except Exception as e:
                logger.warning("Native MLflow run logging failed: %s. Falling back to local file store.", e)

        # 2. Structured Local File Store Logging (Guaranteed zero-dependency fallback)
        run_folder = self.experiment_dir / run_id
        run_folder.mkdir(parents=True, exist_ok=True)

        meta_payload = {
            "run_id": run_id,
            "experiment_name": self.experiment_name,
            "model_name": model_name,
            "created_at_utc": timestamp_utc,
            "params": params,
            "metrics": metrics,
            "tags": tags,
        }

        with open(run_folder / "run_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta_payload, f, indent=2)

        if model_artifact is not None:
            try:
                import pickle
                with open(run_folder / "model.pkl", "wb") as f:
                    pickle.dump(model_artifact, f)
            except Exception as e:
                logger.warning("Could not pickle model artifact: %s", e)

        logger.info("Logged surveillance model run %s for %s", run_id, model_name)
        return run_id

    def log_walk_forward_evaluation(
        self,
        model_name: str,
        fold_metrics: List[Any],
        params: Dict[str, Any],
    ) -> str:
        """
        Logs a walk-forward cross-validation evaluation run, computing aggregated metrics.
        """
        if not fold_metrics:
            raise ValueError("fold_metrics list cannot be empty.")

        # Compute summary averages across folds
        fold_dicts = [m.to_dict() if hasattr(m, "to_dict") else asdict(m) for m in fold_metrics]
        avg_anomaly_rate = float(np.mean([f["test_anomaly_rate"] for f in fold_dicts]))
        avg_anomaly_score = float(np.mean([f["mean_anomaly_score"] for f in fold_dicts]))
        total_test_rows = int(np.sum([f["test_rows"] for f in fold_dicts]))

        metrics = {
            "cv_folds_count": len(fold_dicts),
            "cv_avg_test_anomaly_rate": round(avg_anomaly_rate, 4),
            "cv_avg_anomaly_score": round(avg_anomaly_score, 4),
            "cv_total_test_evaluated_rows": total_test_rows,
        }

        tags = {
            "validation_type": "chronological_walk_forward",
            "folds_evaluated": str(len(fold_dicts)),
        }

        run_id = self.log_training_run(
            model_name=model_name,
            params=params,
            metrics=metrics,
            tags=tags,
        )

        # Write detailed fold-by-fold breakdown into run folder
        run_folder = self.experiment_dir / run_id
        if run_folder.exists():
            with open(run_folder / "fold_breakdown.json", "w", encoding="utf-8") as f:
                json.dump(fold_dicts, f, indent=2)

        return run_id

    def get_run_metadata(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves metadata dictionary for a specific run_id from local storage.
        """
        meta_file = self.experiment_dir / run_id / "run_meta.json"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
