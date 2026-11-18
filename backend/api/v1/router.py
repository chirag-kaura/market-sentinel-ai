"""
API v1 Router Aggregator.
Phase 10 — Step 10.3: Combines alerts, market, investigations, stream, news, and auth routes.
"""

from fastapi import APIRouter
from backend.api.v1.endpoints import alerts, market, investigations, stream, auth, news

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(alerts.router)
api_router.include_router(market.router)
api_router.include_router(news.router)
api_router.include_router(investigations.router)
api_router.include_router(stream.router)
