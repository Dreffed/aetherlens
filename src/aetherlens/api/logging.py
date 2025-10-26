"""
Structured logging configuration for AetherLens.
"""

import logging
import sys
import uuid

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from aetherlens.config import settings


def configure_logging() -> None:
    """Configure structured logging with structlog."""

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.aetherlens_log_level.upper()),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            (
                structlog.processors.JSONRenderer()
                if settings.log_format == "json"
                else structlog.dev.ConsoleRenderer()
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.aetherlens_log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID and log HTTP requests."""

    async def dispatch(self, request: Request, call_next):
        """Add request ID and log request/response."""

        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Bind request ID to context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        logger = structlog.get_logger()
        logger.info("Request started")

        # Process request
        response = await call_next(request)

        # Log response
        logger.info(
            "Request completed",
            status_code=response.status_code,
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
