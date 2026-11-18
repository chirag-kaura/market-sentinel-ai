"""
Unit tests for Clean-Slate Environment Bootstrap Verification (Phase 12 — Step 12.5).
"""

from scripts.bootstrap.verify_clean_slate import audit_clean_slate_filesystem


def test_clean_slate_filesystem_audit():
    passed, issues = audit_clean_slate_filesystem()
    assert passed, f"Clean-slate verification discovered missing components: {issues}"
    assert len(issues) == 0
