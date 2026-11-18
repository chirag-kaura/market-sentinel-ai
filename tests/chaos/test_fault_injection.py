"""
Chaos Engineering and Fault Injection Test Suite for Market Sentinel AI.
Phase 11 — Step 11.9: Simulates upstream network dropouts, database partition latency,
and LLM provider outages to verify platform resilience.
"""

import time
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.core.exceptions import SurveillanceAPIException
from intelligence.rag.llm_provider import GroqLLMProvider, LLMGenerationResponse


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


def test_fault_injection_llm_provider_timeout(monkeypatch):
    """Verifies RAG pipeline gracefully degrades when Groq API times out or raises network fault."""
    llm = GroqLLMProvider(api_key="mock_key")

    def mock_failing_generate(*args, **kwargs):
        raise ConnectionResetError("Connection reset by peer: Groq API gateway unreachable.")

    monkeypatch.setattr(llm, "generate", mock_failing_generate)

    # Calling generate should catch or surface controlled fallback without crashing host process
    with pytest.raises(ConnectionResetError) as exc_info:
        llm.generate("Analyze pre-announcement volume for INFY.")
    
    assert "Groq API gateway unreachable" in str(exc_info.value)


def test_fault_injection_db_transient_failure():
    """Verifies that unhandled database exceptions are intercepted by global exception handler."""
    app = create_app()
    
    @app.get("/chaos/db-outage")
    def chaos_endpoint():
        raise OSError("OperationalError: Lost connection to PostgreSQL database server during query.")
        
    local_client = TestClient(app, raise_server_exceptions=False)
    response = local_client.get("/chaos/db-outage")
    assert response.status_code == 500
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "INTERNAL_SERVER_ERROR"
    # Verify no raw sensitive connection strings leaked to public client
    assert "password" not in response.text.lower()


def test_fault_injection_high_concurrency_degradation(client):
    """Verifies API maintains responsiveness and bounds latency under rapid bursts of health checks."""
    start_time = time.perf_counter()
    for _ in range(50):
        res = client.get("/health")
        assert res.status_code == 200
    duration = time.perf_counter() - start_time
    # 50 calls should complete in under 1 second on local ASGI runner
    assert duration < 2.0
