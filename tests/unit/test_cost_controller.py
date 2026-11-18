"""Unit tests for TokenBudgetCostController (Phase 9 — Step 9.10)."""
import time
import pytest
from intelligence.rag.cost_controller import TokenBudgetCostController


@pytest.fixture
def controller():
    return TokenBudgetCostController(
        max_daily_token_budget=10_000,
        rate_limit_per_minute=5,
        cache_ttl_seconds=2.0
    )


def test_response_caching_and_hit_tracking(controller):
    prompt = "Explain market anomaly for TATAMOTORS."
    resp_text = "Simulated dossier response text."

    # First access: cache miss
    cached = controller.get_cached_response(prompt)
    assert cached is None

    # Store in cache
    controller.store_cached_response(prompt, resp_text, total_tokens=150)

    # Second access: cache hit
    cached_hit = controller.get_cached_response(prompt)
    assert cached_hit == resp_text

    stats = controller.get_usage_stats()
    assert stats.cache_hits == 1
    assert stats.cache_misses == 1


def test_rate_limiting_enforcement(controller):
    # Allowed rate limit is 5 calls per minute
    for _ in range(5):
        assert controller.check_rate_limit()
        controller.record_usage(prompt_tokens=50, completion_tokens=50)

    # 6th call should be throttled
    assert not controller.check_rate_limit()


def test_budget_exceeded_detection(controller):
    # Budget is 10,000 tokens
    controller.record_usage(prompt_tokens=6000, completion_tokens=4500)
    stats = controller.get_usage_stats()

    assert stats.total_tokens == 10500
    assert stats.is_budget_exceeded
    assert stats.estimated_cost_usd > 0.0
