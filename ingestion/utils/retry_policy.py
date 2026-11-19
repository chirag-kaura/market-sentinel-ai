"""Retry policy utilities and resilience patterns for external data source ingestion.

Implements exponential backoff with jitter for HTTP 429 (Rate Limit),
502 (Bad Gateway), 503 (Service Unavailable), and 504 (Gateway Timeout)
using the Tenacity library.
Includes Token Bucket Rate Limiting and Circuit Breaker state management (FR-1.4).
"""
import logging
import threading
import time
from typing import Callable, Any, Optional
import urllib.error
import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 502, 503, 504}


class CircuitBreakerOpenError(RuntimeError):
    """Raised when an external API call is rejected by an open circuit breaker."""
    pass


class TokenBucketRateLimiter:
    """Thread-safe Token Bucket rate limiter for external provider quotas."""

    def __init__(self, capacity: float, refill_rate_per_sec: float):
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.refill_rate = float(refill_rate_per_sec)
        self.last_update = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens: float = 1.0, timeout: Optional[float] = None) -> bool:
        """Acquires tokens, blocking up to `timeout` seconds if necessary."""
        start = time.monotonic()
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self.last_update
                self.last_update = now
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                missing = tokens - self.tokens
                wait_time = missing / self.refill_rate

            if timeout is not None and (time.monotonic() - start + wait_time) > timeout:
                return False

            time.sleep(min(wait_time, 0.1))


class CircuitBreaker:
    """Thread-safe Circuit Breaker pattern preventing cascading provider overload."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout_sec: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_sec
        self.failure_count = 0
        self.state = "CLOSED"  # "CLOSED", "OPEN", "HALF_OPEN"
        self.last_state_change = time.monotonic()
        self._lock = threading.Lock()

    def can_execute(self) -> bool:
        with self._lock:
            now = time.monotonic()
            if self.state == "OPEN":
                if now - self.last_state_change >= self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    self.last_state_change = now
                    logger.info("Circuit breaker transitioned to HALF_OPEN")
                    return True
                return False
            return True

    def record_success(self) -> None:
        with self._lock:
            if self.state == "HALF_OPEN":
                logger.info("Circuit breaker recovered: transitioning to CLOSED")
            self.state = "CLOSED"
            self.failure_count = 0

    def record_failure(self) -> None:
        with self._lock:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                self.last_state_change = time.monotonic()
                logger.warning(
                    "Circuit breaker tripped to OPEN after %d consecutive failures. Cooling down for %.1fs",
                    self.failure_count,
                    self.recovery_timeout,
                )


def is_retryable_exception(exc: BaseException) -> bool:
    """Determine whether an HTTP or network exception qualifies for retry."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS_CODES
    if isinstance(exc, (httpx.RequestError, httpx.TimeoutException)):
        return True
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in RETRYABLE_STATUS_CODES
    if isinstance(exc, urllib.error.URLError):
        return True
    return False


def ingestion_retry(
    max_attempts: int = 4,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    circuit_breaker: Optional[CircuitBreaker] = None,
    rate_limiter: Optional[TokenBucketRateLimiter] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to retry network ingestion calls with exponential backoff, jitter,
    circuit breaking, and rate limiting."""
    base_decorator = retry(
        retry=retry_if_exception(is_retryable_exception),
        wait=wait_exponential_jitter(initial=initial_delay, max=max_delay),
        stop=stop_after_attempt(max_attempts),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        retried_fn = base_decorator(fn)

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if circuit_breaker and not circuit_breaker.can_execute():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. Upstream call to {fn.__name__} blocked to prevent provider ban."
                )

            if rate_limiter:
                rate_limiter.acquire(1.0, timeout=10.0)

            try:
                result = retried_fn(*args, **kwargs)
                if circuit_breaker:
                    circuit_breaker.record_success()
                return result
            except Exception as exc:
                if circuit_breaker and is_retryable_exception(exc):
                    circuit_breaker.record_failure()
                raise

        return wrapper

    return decorator
