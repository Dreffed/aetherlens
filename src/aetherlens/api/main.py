"""
AetherLens FastAPI Application
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from aetherlens.config import settings
from aetherlens.api.database import db_manager
from aetherlens.api.logging import configure_logging, RequestLoggingMiddleware
from aetherlens.api.rate_limit import RateLimitMiddleware
from aetherlens.api.metrics import PrometheusMiddleware, metrics_endpoint
from aetherlens.api.routes import auth, health, devices


logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan handler for startup/shutdown tasks.

    Manages:
    - Database connection pool
    - Plugin manager initialization
    - Background task cleanup
    """
    logger.info("Starting AetherLens API", version="1.0.0")

    # Startup
    await db_manager.connect()
    logger.info("Database connected", pool_size=settings.database_pool_size)

    yield

    # Shutdown
    logger.info("Shutting down AetherLens API")
    await db_manager.disconnect()
    logger.info("Database disconnected")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    # Configure logging first
    configure_logging()

    app = FastAPI(
        title="AetherLens Home Edition",
        description="Cost and usage monitoring for home labs, smart homes, and IoT devices",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on environment
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Rate limiting middleware
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=60,
        requests_per_hour=1000
    )

    # Prometheus metrics middleware
    app.add_middleware(PrometheusMiddleware)

    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # Include routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(devices.router)

    return app


app = create_app()


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return await metrics_endpoint()


# Root endpoint - basic health check
@app.get("/")
async def root():
    """Root endpoint - basic health check."""
    return {
        "service": "AetherLens Home Edition",
        "version": "1.0.0",
        "status": "running"
    }
