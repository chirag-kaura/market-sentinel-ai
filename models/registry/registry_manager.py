"""
Continuous MLflow Production Registry and Model Lineage Manager.
Phase 11 — Step 11.7: Tracks anomaly model versions, parameters, metrics, and production promotion.
"""

from typing import Dict, List, Optional
import os
import json
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ModelArtifactMeta(BaseModel):
    model_name: str
    version: str
    stage: str  # STAGING, PRODUCTION, ARCHIVED
    registered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    hyperparameters: Dict[str, float]
    metrics: Dict[str, float]
    artifact_uri: str


class MLflowProductionRegistry:
    """Manages versioned model artifacts and stage transitions with filesystem persistence."""

    def __init__(self, registry_path: str = "models/registry/model_catalog.json"):
        self.registry_path = registry_path
        self._catalog: Dict[str, List[ModelArtifactMeta]] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r") as f:
                    data = json.load(f)
                    for name, models in data.items():
                        self._catalog[name] = [ModelArtifactMeta(**m) for m in models]
            except Exception:
                self._catalog = {}

    def _save(self):
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        data = {name: [m.model_dump() for m in models] for name, models in self._catalog.items()}
        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def register_model_version(
        self,
        model_name: str,
        version: str,
        hyperparameters: Dict[str, float],
        metrics: Dict[str, float],
        artifact_uri: str,
        stage: str = "STAGING",
    ) -> ModelArtifactMeta:
        """Registers a new candidate surveillance model version."""
        meta = ModelArtifactMeta(
            model_name=model_name,
            version=version,
            stage=stage,
            hyperparameters=hyperparameters,
            metrics=metrics,
            artifact_uri=artifact_uri,
        )
        if model_name not in self._catalog:
            self._catalog[model_name] = []
        self._catalog[model_name].append(meta)
        self._save()
        return meta

    def transition_stage(
        self, model_name: str, version: str, new_stage: str
    ) -> Optional[ModelArtifactMeta]:
        """Transitions a model version to PRODUCTION, ARCHIVED, or STAGING."""
        if model_name not in self._catalog:
            return None

        target_meta = None
        for m in self._catalog[model_name]:
            if m.version == version:
                m.stage = new_stage
                target_meta = m
            elif new_stage == "PRODUCTION" and m.stage == "PRODUCTION":
                # Demote previous production model to ARCHIVED
                m.stage = "ARCHIVED"

        self._save()
        return target_meta

    def get_production_model(self, model_name: str) -> Optional[ModelArtifactMeta]:
        """Retrieves currently active PRODUCTION model metadata."""
        if model_name not in self._catalog:
            return None
        for m in self._catalog[model_name]:
            if m.stage == "PRODUCTION":
                return m
        return None
