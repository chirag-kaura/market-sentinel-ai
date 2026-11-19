"""
FastAPI Main Application Factory.
Phase 10 — Step 10.1: Centralized ASGI application factory mounting middleware,
global exception handlers, health/readiness probes, and API routers.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os
from typing import Dict
from fastapi import FastAPI, status

logger = logging.getLogger("market_sentinel.main")
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.core.exceptions import (
    SurveillanceAPIException,
    surveillance_exception_handler,
    global_unhandled_exception_handler,
)


def _publish_drift_metrics_sync() -> None:
    """Computes feature PSI drift across ALL monitored NSE symbols from PostgreSQL 16."""
    import pandas as pd
    from backend.core.database import SessionLocal
    from backend.models.market import MarketFeatureDailyModel, SymbolMasterModel
    from backend.core.metrics import record_feature_drift
    from monitoring.drift.drift_detector import DriftDetector

    db = SessionLocal()
    try:
        symbols = [s.symbol for s in db.query(SymbolMasterModel).all()]
        detector = DriftDetector()
        for sym in symbols:
            rows = (
                db.query(MarketFeatureDailyModel)
                .filter_by(symbol=sym)
                .order_by(MarketFeatureDailyModel.feature_date)
                .all()
            )
            if len(rows) < 40:
                continue
            df = pd.DataFrame(
                [
                    {
                        "log_return_1d": float(r.return_daily),
                        "volatility_20d": float(r.volatility_roll_20d),
                        "volume_zscore_20d": float(r.volume_zscore_20d),
                        "delivery_zscore_20d": float(r.delivery_zscore_20d or 0.0),
                    }
                    for r in rows
                ]
            )
            split = int(len(df) * 0.70)
            report = detector.run_drift_audit(df.iloc[:split], df.iloc[split:], list(df.columns))
            for feat_name, metric in report.metrics.items():
                record_feature_drift(sym, feat_name, round(metric.psi_score, 4))
    except Exception as exc:
        logger.warning("Drift metrics publish skipped: %s", exc)
    finally:
        db.close()


async def _background_news_refresh_loop(interval_seconds: int = 900):
    """Periodically refreshes authentic RSS news, announcements & drift metrics into PostgreSQL 16."""
    from backend.core.database import SessionLocal
    from scripts.ingest_real_market_data import (
        ingest_real_news_articles,
        ingest_real_corporate_announcements,
    )

    # Publish initial drift metrics on startup
    await asyncio.to_thread(_publish_drift_metrics_sync)

    while True:
        await asyncio.sleep(interval_seconds)
        try:
            def _run_sync_refresh():
                db = SessionLocal()
                try:
                    ingest_real_news_articles(db)
                    ingest_real_corporate_announcements(db)
                finally:
                    db.close()
                _publish_drift_metrics_sync()

            await asyncio.to_thread(_run_sync_refresh)
            logger.info("Background auto-refresh completed: news, announcements & drift metrics updated.")
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.warning("Background auto-refresh skipped due to error: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for clean startup and shutdown events."""
    refresh_task = asyncio.create_task(_background_news_refresh_loop(interval_seconds=900))
    alert_stream_task = None
    if os.getenv("DISABLE_REDPANDA_CONSUMER", "0") != "1" and "PYTEST_CURRENT_TEST" not in os.environ:
        from streaming.live_bridge import poll_live_alerts_to_sse_loop

        alert_stream_task = asyncio.create_task(poll_live_alerts_to_sse_loop())

    yield

    refresh_task.cancel()
    if alert_stream_task is not None:
        alert_stream_task.cancel()
    try:
        await refresh_task
    except asyncio.CancelledError:
        pass
    if alert_stream_task is not None:
        try:
            await alert_stream_task
        except asyncio.CancelledError:
            pass


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
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:30080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:30080",
        ],
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

    @app.get("/ready", tags=["System Telemetry"])
    async def readiness_check(response: Response) -> Dict[str, str]:
        """
        Readiness probe verifying operational state across dependent subsystems:
        1. PostgreSQL / SQLite Database Connectivity
        2. Statistical & Anomaly Inference Subsystems
        """
        from backend.core.database import engine
        from sqlalchemy import text

        checks: Dict[str, str] = {}
        is_ready = True

        # 1. Database Health Check
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            checks["database"] = "connected"
        except Exception as exc:
            checks["database"] = f"unhealthy: {str(exc)}"
            is_ready = False

        # 2. Inference Engine Check
        try:
            from models.inference.ensemble_engine import SurveillanceEnsembleEngine
            engine_inst = SurveillanceEnsembleEngine()
            health = engine_inst.health_check()
            checks["inference_engine"] = health.get("status", "ready")
        except Exception as exc:
            checks["inference_engine"] = f"unhealthy: {str(exc)}"
            is_ready = False

        if not is_ready:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return {
            "status": "ready" if is_ready else "degraded",
            "database": checks.get("database", "unknown"),
            "inference_engine": checks.get("inference_engine", "unknown"),
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
