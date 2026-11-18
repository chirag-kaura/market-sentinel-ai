"""
Centralized Error Tracking and Sentry SDK Integration.
Phase 11 — Step 11.6: Initializes Sentry error tracking with graceful fallback when sentry-sdk is optional.
"""

import os
from typing import Optional

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    HAS_SENTRY = True
except ImportError:
    sentry_sdk = None
    FastApiIntegration = None
    LoggingIntegration = None
    HAS_SENTRY = False


def init_sentry(
    dsn: Optional[str] = None,
    environment: str = "production",
    traces_sample_rate: float = 0.1,
) -> bool:
    """
    Initializes Sentry error tracking with PII stripping and custom tracing rate.
    Returns True if initialized, False if DSN is missing or sentry_sdk is not installed.
    """
    effective_dsn = dsn or os.getenv("SENTRY_DSN")
    if not effective_dsn or not HAS_SENTRY:
        return False

    def before_send(event, hint):
        # Scrub sensitive authorization tokens or cookie values from error breadcrumbs
        if "request" in event:
            headers = event["request"].get("headers", {})
            if "Authorization" in headers:
                headers["Authorization"] = "[REDACTED]"
            if "Cookie" in headers:
                headers["Cookie"] = "[REDACTED]"
        return event

    integrations = []
    if FastApiIntegration:
        integrations.append(FastApiIntegration())
    if LoggingIntegration:
        integrations.append(LoggingIntegration(level=None, event_level=None))

    sentry_sdk.init(
        dsn=effective_dsn,
        environment=environment,
        traces_sample_rate=traces_sample_rate,
        before_send=before_send,
        integrations=integrations,
    )
    return True

