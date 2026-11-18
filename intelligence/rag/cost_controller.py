"""
Token Budgeting, Response Caching, and Cost Control Engine.
Phase 9 — Step 9.10: Manages LLM token consumption limits, caches recurring dossier queries,
enforces request rate-limiting, and tracks cumulative API expenditure.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import time
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class CachedLLMResponse:
    """Cached LLM completion record."""
    cache_key: str
    response_content: str
    cached_at: float
    total_tokens: int


@dataclass(frozen=True)
class BudgetUsageStats:
    """Usage and budgeting telemetry."""
    total_calls: int
    cache_hits: int
    cache_misses: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    is_budget_exceeded: bool


class TokenBudgetCostController:
    """
    Prevents API quota runaway and cost spikes in surveillance RAG execution.
    Features:
    1. In-memory response cache with TTL (Time-To-Live).
    2. Token budget enforcement with graceful throttling.
    3. Rolling rate-limiter (calls per minute).
    4. Accurate token-to-cost modeling (Groq baseline pricing).
    """

    # Estimated Groq pricing baseline per 1,000,000 tokens ($0.05 prompt, $0.08 completion for Llama 8B)
    PRICE_PER_M_PROMPT = 0.05
    PRICE_PER_M_COMPLETION = 0.08

    def __init__(
        self,
        max_daily_token_budget: int = 2_000_000,
        rate_limit_per_minute: int = 60,
        cache_ttl_seconds: float = 3600.0  # 1 hour default cache
    ):
        self.max_budget = max_daily_token_budget
        self.rate_limit = rate_limit_per_minute
        self.cache_ttl = cache_ttl_seconds

        self._cache: Dict[str, CachedLLMResponse] = {}
        self._call_timestamps: list[float] = []
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._cache_hits = 0
        self._cache_misses = 0

    def check_rate_limit(self) -> bool:
        """Returns True if within rate limit; False if throttled."""
        now = time.time()
        # Keep calls within past 60 seconds
        self._call_timestamps = [t for t in self._call_timestamps if now - t < 60.0]
        if len(self._call_timestamps) >= self.rate_limit:
            return False
        return True

    def get_cached_response(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Retrieves cached completion if available and not expired."""
        key = self._generate_cache_key(prompt, system_prompt)
        entry = self._cache.get(key)
        if entry is not None:
            if time.time() - entry.cached_at <= self.cache_ttl:
                self._cache_hits += 1
                return entry.response_content
            else:
                del self._cache[key]
        self._cache_misses += 1
        return None

    def store_cached_response(
        self,
        prompt: str,
        response_content: str,
        system_prompt: Optional[str] = None,
        total_tokens: int = 0
    ) -> None:
        """Stores a generated completion in cache."""
        key = self._generate_cache_key(prompt, system_prompt)
        self._cache[key] = CachedLLMResponse(
            cache_key=key,
            response_content=response_content,
            cached_at=time.time(),
            total_tokens=total_tokens
        )

    def record_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Records token usage and registers API call timestamp."""
        self._prompt_tokens += prompt_tokens
        self._completion_tokens += completion_tokens
        self._call_timestamps.append(time.time())

    def get_usage_stats(self) -> BudgetUsageStats:
        """Returns real-time usage statistics and budget status."""
        total_tok = self._prompt_tokens + self._completion_tokens
        cost = (
            (self._prompt_tokens / 1_000_000 * self.PRICE_PER_M_PROMPT) +
            (self._completion_tokens / 1_000_000 * self.PRICE_PER_M_COMPLETION)
        )
        total_calls = len(self._call_timestamps) + self._cache_hits

        return BudgetUsageStats(
            total_calls=total_calls,
            cache_hits=self._cache_hits,
            cache_misses=self._cache_misses,
            total_prompt_tokens=self._prompt_tokens,
            total_completion_tokens=self._completion_tokens,
            total_tokens=total_tok,
            estimated_cost_usd=round(cost, 6),
            is_budget_exceeded=total_tok >= self.max_budget
        )

    @staticmethod
    def _generate_cache_key(prompt: str, system_prompt: Optional[str]) -> str:
        raw = f"{system_prompt or ''}###{prompt}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()
