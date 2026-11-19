"""
Real-time Server-Sent Events (SSE) Streaming Endpoint.
Phase 10 — Step 10.4: Streams realistic incoming surveillance risk events from the catalog.
Once all events have been published, sends a terminal keepalive status rather than looping.
"""

import asyncio
import json
from typing import AsyncGenerator, List, Optional
from fastapi import APIRouter, Request, Query, Security
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from backend.core.security import security_scheme, get_user_from_token, get_current_user
from backend.core.exceptions import SurveillanceAPIException
from backend.services.surveillance_catalog import get_catalog_alerts
from fastapi import status

router = APIRouter(prefix="/stream", tags=["Streaming"])


class AlertStreamBroker:
    """Thread-safe and async-safe pub/sub broker for real-time surveillance streaming (Issue 47)."""
    _subscribers: List[asyncio.Queue] = []

    @classmethod
    def subscribe(cls) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        cls._subscribers.append(q)
        return q

    @classmethod
    def unsubscribe(cls, q: asyncio.Queue) -> None:
        if q in cls._subscribers:
            cls._subscribers.remove(q)

    @classmethod
    async def publish_alert(cls, alert_dict: dict) -> None:
        """Broadcast newly detected alert to all active EventSource clients."""
        for q in list(cls._subscribers):
            try:
                await q.put(alert_dict)
            except Exception:
                pass


def authenticate_stream_request(
    token: Optional[str] = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
):
    """Authenticate stream subscriber via Bearer header or query token parameter."""
    token_str = credentials.credentials if credentials else token
    if not token_str:
        raise SurveillanceAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="MISSING_TOKEN",
            message="Streaming authentication requires Bearer token or ?token= query parameter.",
        )
    return get_user_from_token(token_str)


async def alert_event_generator(request: Request, max_events: int = 0) -> AsyncGenerator[str, None]:
    """
    Asynchronously yields Server-Sent Events formatted alert payloads.
    Emits initial catalog backlog, then listens to real-time events via AlertStreamBroker.
    """
    q = AlertStreamBroker.subscribe()
    event_count = 0

    try:
        # 1. Stream initial active alerts
        catalog = get_catalog_alerts()
        for alert in catalog:
            if await request.is_disconnected():
                return

            event_data = {
                "event_id": alert.alert_id,
                "timestamp": alert.event_timestamp.isoformat(),
                "ticker": alert.ticker,
                "anomaly_type": alert.anomaly_category,
                "composite_risk_score": alert.composite_risk_score,
                "priority": alert.priority_level,
                "summary_explanation": alert.summary_explanation,
                "feed_source": "CATALOG_REPLAY",
            }
            yield f"event: alert\ndata: {json.dumps(event_data)}\n\n"
            event_count += 1
            if max_events > 0 and event_count >= max_events:
                return

            await asyncio.sleep(2.0)

        # 2. Listen for live events from pipeline broker
        while not await request.is_disconnected():
            try:
                live_event = await asyncio.wait_for(q.get(), timeout=12.0)
                yield f"event: alert\ndata: {json.dumps(live_event)}\n\n"
                event_count += 1
                if max_events > 0 and event_count >= max_events:
                    return
            except asyncio.TimeoutError:
                # Keepalive heartbeat
                yield ": heartbeat\n\n"
    finally:
        AlertStreamBroker.unsubscribe(q)


@router.get("/alerts")
async def stream_alerts(
    request: Request,
    limit: int = 0,
    token: Optional[str] = Query(None, description="Optional JWT token for browser EventSource authentication"),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
):
    """
    Server-Sent Events endpoint for real-time risk alert push.
    Clients connect via EventSource in the web UI.
    Requires Bearer token or ?token= query parameter.
    """
    authenticate_stream_request(token=token, credentials=credentials)
    return StreamingResponse(
        alert_event_generator(request, max_events=limit),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Stream-Mode": "CATALOG_REPLAY",
        },
    )
