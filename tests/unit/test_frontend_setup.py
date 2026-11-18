"""
Verification test for Frontend Setup, Contracts, and API Client integration.
Phase 10 — Step 10.6.
"""

import json
from pathlib import Path


def test_frontend_project_structure():
    frontend_dir = Path("frontend")
    assert frontend_dir.exists()
    assert (frontend_dir / "package.json").exists()
    assert (frontend_dir / "tsconfig.json").exists()
    assert (frontend_dir / "tailwind.config.js").exists()


def test_package_json_dependencies():
    pkg_file = Path("frontend/package.json")
    with open(pkg_file, "r") as f:
        pkg = json.load(f)
    assert pkg["name"] == "market-sentinel-ui"
    assert "react" in pkg["dependencies"]
    assert "tailwindcss" in pkg["devDependencies"]
    assert "typescript" in pkg["devDependencies"]


def test_typescript_contracts_exist():
    types_file = Path("frontend/src/types/index.ts")
    assert types_file.exists()
    content = types_file.read_text(encoding="utf-8")
    assert "export interface AlertSummary" in content
    assert "export interface AlertDetail" in content
    assert "export interface InvestigationCase" in content
