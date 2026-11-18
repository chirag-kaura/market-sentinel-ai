"""Unit tests for Decoupled LLM Provider Abstraction (Phase 9 — Step 9.6)."""
import pytest
from intelligence.rag.llm_provider import MockLLMProvider, GroqLLMProvider, BaseLLMProvider


def test_mock_llm_provider_generation():
    provider: BaseLLMProvider = MockLLMProvider(model_name="test-mock-llm")

    res = provider.generate("Summarize market anomaly for RELIANCE.")

    assert res.is_mock
    assert res.model_name == "test-mock-llm"
    assert res.content is not None
    assert res.total_tokens > 0
    assert provider.health_check()


def test_mock_llm_structured_generation():
    provider: BaseLLMProvider = MockLLMProvider()

    res = provider.generate_structured("Generate structured alert dossier for TATAMOTORS.")

    assert res.is_mock
    assert res.structured_data is not None
    assert "alert_summary" in res.structured_data
    assert "evidence_citations" in res.structured_data
    assert not res.structured_data["insufficient_evidence"]


def test_groq_llm_provider_fallback_without_keys():
    # Verify that without API key, Groq provider falls back safely without raising uncaught exceptions
    provider = GroqLLMProvider(api_key=None, model_name="llama-3.1-8b-instant")

    res = provider.generate("Test prompt")
    assert res is not None
    assert res.is_mock
    assert provider.health_check()
