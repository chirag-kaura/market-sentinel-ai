"""
Unit tests for Sentry Centralized Error Tracking (Phase 11 — Step 11.6).
"""

import pytest
from backend.core.sentry import init_sentry


def test_init_sentry_without_dsn():
    # Should safely return False without raising exceptions
    initialized = init_sentry(dsn=None)
    assert not initialized


def test_init_sentry_with_mock_dsn(monkeypatch):
    mock_dsn = "https://mockkey@o0.ingest.sentry.io/0"
    
    # Mock HAS_SENTRY and sentry_sdk
    import backend.core.sentry as sentry_mod
    monkeypatch.setattr(sentry_mod, "HAS_SENTRY", True)
    
    class MockSentrySdk:
        @staticmethod
        def init(**kwargs):
            pass
            
    monkeypatch.setattr(sentry_mod, "sentry_sdk", MockSentrySdk)
    
    initialized = sentry_mod.init_sentry(dsn=mock_dsn, environment="test")
    assert initialized
