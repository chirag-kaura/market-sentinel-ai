"""
Verification test for Minikube Kubernetes Manifests.
Phase 12 — Step 12.4.
"""

from pathlib import Path
import yaml


def test_k8s_manifests_structure():
    manifest_file = Path("deployment/k8s/sentinel_app.yaml")
    assert manifest_file.exists()

    with open(manifest_file, "r") as f:
        docs = list(yaml.safe_load_all(f))

    assert len(docs) >= 5

    kinds = [d["kind"] for d in docs]
    assert "Namespace" in kinds
    assert "Deployment" in kinds
    assert "Service" in kinds

    # Verify resource requests and limits in Deployments
    deployments = [d for d in docs if d["kind"] == "Deployment"]
    for dep in deployments:
        containers = dep["spec"]["template"]["spec"]["containers"]
        for c in containers:
            assert "resources" in c
            assert "limits" in c["resources"]
            assert "memory" in c["resources"]["limits"]
            assert "cpu" in c["resources"]["limits"]
            assert "livenessProbe" in c
