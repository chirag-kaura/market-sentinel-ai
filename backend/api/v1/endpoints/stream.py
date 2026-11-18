"""
Real-time Server-Sent Events (SSE) Streaming Endpoint.
Phase 10 — Step 10.4: Streams realistic incoming surveillance risk events from the catalog.
Once all events have been published, sends a terminal keepalive status rather than looping.
"""

import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from backend.services.surveillance_catalog import get_catalog_alerts

router = APIRouter(prefix="/stream", tags=["Streaming"])


async def alert_event_generator(request: Request, max_events: int = 0) -> AsyncGenerator[str, None]:
    """
    Asynchronously yields Server-Sent Events formatted alert payloads.
    Emits distinct events sequentially from the catalog at realistic intervals.
    Does NOT repeat or cycle identically once all alerts have aired.
    """
    alerts = get_catalog_alerts()
    event_count = 0

    for alert in alerts:
        if await request.is_disconnected():
            break

        event_data = {
            "event_id": alert.alert_id,
            "timestamp": alert.event_timestamp.isoformat(),
            "ticker": alert.ticker,
            "anomaly_type": alert.anomaly_category,
            "composite_risk_score": alert.composite_risk_score,
            "priority": alert.priority_level,
            "summary_explanation": alert.summary_explanation,
        }

        yield f"event: alert\ndata: {json.dumps(event_data)}\n\n"
        event_count += 1

        if max_events > 0 and event_count >= max_events:
            return

        # 6 seconds between distinct equity events
        await asyncio.sleep(6.0)

    # After publishing all alerts, stream lightweight heartbeat keepalives
    while not await request.is_disconnected():
        yield ": heartbeat\n\n"
        await asyncio.sleep(15.0)


@router.get("/alerts")
async def stream_alerts(request: Request, limit: int = 0):
    """
    Server-Sent Events endpoint for real-time risk alert push.
    Clients connect via EventSource in the web UI.
    """
    return StreamingResponse(
        alert_event_generator(request, max_events=limit),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
