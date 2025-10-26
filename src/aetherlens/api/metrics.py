"""
Prometheus metrics for API monitoring.
"""

import time
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

logger = structlog.get_logger()


# Define metrics
REQUEST_COUNT = Counter(
    "aetherlens_api_requests_total", "Total API requests", ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "aetherlens_api_request_duration_seconds", "API request duration", ["method", "endpoint"]
)

REQUEST_IN_PROGRESS = Gauge(
    "aetherlens_api_requests_in_progress",
    "API requests currently being processed",
    ["method", "endpoint"],
)

DATABASE_POOL_SIZE = Gauge("aetherlens_database_pool_size", "Database connection pool size")

DATABASE_POOL_AVAILABLE = Gauge(
    "aetherlens_database_pool_available", "Available database connections"
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Collect metrics for each request."""

        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        path = request.url.path

        # Track in-progress requests
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=path).inc()

        # Time request
        start_time = time.time()

        try:
            response: Response = await call_next(request)

            # Record metrics
            duration = time.time() - start_time
            REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)
            REQUEST_COUNT.labels(method=method, endpoint=path, status=response.status_code).inc()

            return response

        finally:
            REQUEST_IN_PROGRESS.labels(method=method, endpoint=path).dec()


async def metrics_endpoint() -> StarletteResponse:
    """
    Expose Prometheus metrics.

    Returns metrics in Prometheus text format.
    """
    # Update database pool metrics if available
    try:
        from aetherlens.api.database import db_manager

        pool = db_manager.get_pool()
        if pool:
            DATABASE_POOL_SIZE.set(pool.get_size())
            DATABASE_POOL_AVAILABLE.set(pool.get_size() - pool.get_idle_size())
    except Exception as e:
        logger.error("Failed to update pool metrics", error=str(e))

    # Generate metrics
    metrics_data = generate_latest()

    return StarletteResponse(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
