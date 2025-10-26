"""
Health check endpoints for monitoring.
"""

import asyncio
from datetime import datetime
from typing import Any

import structlog
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from aetherlens.api.database import db_manager

logger = structlog.get_logger()
router = APIRouter(tags=["Health"])


class HealthStatus(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    version: str
    checks: dict[str, dict[str, Any]]


async def check_database() -> dict[str, Any]:
    """Check database connectivity and responsiveness."""
    try:
        pool = db_manager.get_pool()
        start = asyncio.get_event_loop().time()

        async with pool.acquire() as conn:
            _ = await conn.fetchval("SELECT 1")  # Connection health check

        latency_ms = (asyncio.get_event_loop().time() - start) * 1000

        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "message": "Database responding",
        }

    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return {"status": "unhealthy", "error": str(e), "message": "Database connection failed"}


async def check_timescaledb() -> dict[str, Any]:
    """Check TimescaleDB extension status."""
    try:
        pool = db_manager.get_pool()

        async with pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb'"
            )

        if result:
            return {
                "status": "healthy",
                "version": result["extversion"],
                "message": "TimescaleDB active",
            }
        return {"status": "unhealthy", "message": "TimescaleDB extension not found"}

    except Exception as e:
        logger.error("TimescaleDB check failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Comprehensive health check for all dependencies.

    Returns service status and health of:
    - Database connection
    - TimescaleDB extension
    - Overall service health

    **Status Codes:**
    - 200: All checks passed (healthy)
    - 503: One or more checks failed (unhealthy)
    """
    # Run all checks concurrently
    db_check, timescale_check = await asyncio.gather(
        check_database(), check_timescaledb(), return_exceptions=True
    )

    # Determine overall status
    all_healthy = all(
        check.get("status") == "healthy"
        for check in [db_check, timescale_check]
        if isinstance(check, dict)
    )

    response = HealthStatus(
        status="healthy" if all_healthy else "unhealthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        checks={
            "database": db_check if isinstance(db_check, dict) else {"status": "error"},
            "timescaledb": (
                timescale_check if isinstance(timescale_check, dict) else {"status": "error"}
            ),
        },
    )

    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(content=response.model_dump(), status_code=status_code)


@router.get("/health/ready")
async def readiness_check():
    """
    Kubernetes-style readiness probe.

    Returns 200 if service is ready to accept traffic.
    Returns 503 if service is starting up or dependencies unavailable.
    """
    try:
        pool = db_manager.get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        return {"status": "ready"}

    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "reason": str(e)},
        )


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe.

    Returns 200 if service process is alive.
    This is a simple check that doesn't verify dependencies.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
