"""
Verification test for GitHub Actions CI/CD Pipeline Configuration.
Phase 11 — Step 11.8.
"""

from pathlib import Path
import yaml


def test_ci_workflow_yaml_structure():
    workflow_file = Path(".github/workflows/ci.yml")
    assert workflow_file.exists()

    with open(workflow_file, "r") as f:
        wf = yaml.safe_load(f)

    assert "on" in wf
    assert "jobs" in wf
    assert "backend-quality-and-test" in wf["jobs"]

    job = wf["jobs"]["backend-quality-and-test"]
    assert job["runs-on"] == "ubuntu-latest"

    # Verify key steps exist in job
    steps = job["steps"]
    step_names = [s.get("name", "") for s in steps]
    
    assert any("Check out" in name for name in step_names)
    assert any("Set up Python" in name for name in step_names)
    assert any("Install Dependencies" in name for name in step_names)
    assert any("Execute Full Automated Test Suite" in name for name in step_names)
