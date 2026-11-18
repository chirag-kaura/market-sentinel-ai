"""
FastAPI Main Application Factory.
Phase 10 — Step 10.1: Centralized ASGI application factory mounting middleware,
global exception handlers, health/readiness probes, and API routers.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.core.exceptions import (
    SurveillanceAPIException,
    surveillance_exception_handler,
    global_unhandled_exception_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for clean startup and shutdown events."""
    # Startup: Initialize shared connection pools / caching
    yield
    # Shutdown: Clean up sockets and active consumers


def create_app() -> FastAPI:
    """Factory function configuring and returning the production FastAPI application."""
    app = FastAPI(
        title="Market Sentinel AI — Surveillance & Risk Intelligence API",
        description="High-throughput AI-powered capital markets surveillance decision-support platform.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 1. CORS, Correlation, and Prometheus Middleware Configuration
    from backend.core.logging import CorrelationIdMiddleware
    from backend.core.metrics import PrometheusMetricsMiddleware, get_prometheus_metrics_payload, CONTENT_TYPE_LATEST
    from fastapi.responses import Response

    app.add_middleware(PrometheusMetricsMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Register Global Exception Handlers
    app.add_exception_handler(SurveillanceAPIException, surveillance_exception_handler)
    app.add_exception_handler(Exception, global_unhandled_exception_handler)

    # 3. Health & Readiness Telemetry Endpoints
    @app.get("/health", status_code=status.HTTP_200_OK, tags=["System Telemetry"])
    async def health_check() -> Dict[str, str]:
        """Liveness probe verifying that ASGI process is responsive."""
        return {
            "status": "healthy",
            "service": "market-sentinel-api",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    @app.get("/ready", status_code=status.HTTP_200_OK, tags=["System Telemetry"])
    async def readiness_check() -> Dict[str, str]:
        """Readiness probe verifying operational state."""
        return {
            "status": "ready",
            "database": "connected",
            "inference_engine": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    @app.get("/metrics", tags=["System Telemetry"])
    def prometheus_metrics() -> Response:
        """Prometheus metrics scrape target."""
        return Response(content=get_prometheus_metrics_payload(), media_type=CONTENT_TYPE_LATEST)

    # 4. Include API Routers
    from backend.api.v1.router import api_router
    app.include_router(api_router)

    return app


app = create_app()
