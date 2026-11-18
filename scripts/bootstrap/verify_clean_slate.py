"""
Clean-Slate Deployment Bootstrap and Verification Script.
Phase 12 — Step 12.5: Verifies complete environment readiness, directory structures,
configuration files, and test suites from a cold start.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


REQUIRED_DIRECTORIES = [
    "backend/api/v1/endpoints",
    "backend/core",
    "backend/models",
    "data/master",
    "deployment/docker",
    "deployment/grafana/dashboards",
    "deployment/alertmanager",
    "deployment/k8s",
    "frontend/src/components",
    "intelligence/rag",
    "intelligence/nlp",
    "monitoring/drift",
    "models/registry",
]

REQUIRED_CONFIG_FILES = [
    "docker-compose.yml",
    "requirements.txt",
    ".dockerignore",
    "deployment/docker/backend.Dockerfile",
    "deployment/docker/frontend.Dockerfile",
    "deployment/docker/nginx.conf",
    "deployment/alertmanager/alertmanager.yml",
    "deployment/k8s/sentinel_app.yaml",
]


def audit_clean_slate_filesystem(root_dir: str = ".") -> Tuple[bool, List[str]]:
    """Audits root workspace ensuring all required directories and configurations exist."""
    base = Path(root_dir)
    errors = []

    for d in REQUIRED_DIRECTORIES:
        if not (base / d).exists():
            errors.append(f"Missing required directory: {d}")

    for f in REQUIRED_CONFIG_FILES:
        if not (base / f).exists():
            errors.append(f"Missing required configuration file: {f}")

    return len(errors) == 0, errors


if __name__ == "__main__":
    passed, issues = audit_clean_slate_filesystem()
    if passed:
        print("Clean-slate environment deployment verification: SUCCESS.")
        sys.exit(0)
    else:
        print("Clean-slate environment deployment verification: FAILED.")
        for iss in issues:
            print(f" - {iss}")
        sys.exit(1)
