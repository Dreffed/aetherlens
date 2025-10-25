"""
Health check endpoint tests.

Tests for:
- GET /health - Comprehensive health check
- GET /health/ready - Kubernetes readiness probe
- GET /health/live - Kubernetes liveness probe
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_success(api_client: AsyncClient):
    """Test main health check endpoint returns healthy status."""
    response = await api_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "checks" in data

    # Verify status is healthy
    assert data["status"] in ["healthy", "degraded"]

    # Verify checks structure
    assert "database" in data["checks"]
    assert "timescaledb" in data["checks"]


@pytest.mark.asyncio
async def test_health_check_database_status(api_client: AsyncClient):
    """Test that health check includes database status."""
    response = await api_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    db_check = data["checks"]["database"]
    assert "status" in db_check

    if db_check["status"] == "healthy":
        # Should include latency for healthy database
        assert "latency_ms" in db_check
        assert db_check["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_health_check_timescaledb_status(api_client: AsyncClient):
    """Test that health check includes TimescaleDB extension status."""
    response = await api_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    ts_check = data["checks"]["timescaledb"]
    assert "status" in ts_check


@pytest.mark.asyncio
async def test_readiness_probe_success(api_client: AsyncClient):
    """Test Kubernetes readiness probe endpoint."""
    response = await api_client.get("/health/ready")

    # Should return 200 if ready, 503 if not
    assert response.status_code in [200, 503]
    data = response.json()

    assert "status" in data
    assert data["status"] in ["ready", "not_ready"]


@pytest.mark.asyncio
async def test_liveness_probe_success(api_client: AsyncClient):
    """Test Kubernetes liveness probe endpoint."""
    response = await api_client.get("/health/live")

    # Liveness should almost always return 200
    # (only fails if app is completely broken)
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_check_no_auth_required(api_client: AsyncClient):
    """Verify health endpoints don't require authentication."""
    # Should work without Authorization header
    response = await api_client.get("/health")
    assert response.status_code == 200

    response = await api_client.get("/health/ready")
    assert response.status_code in [200, 503]

    response = await api_client.get("/health/live")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_check_response_time(api_client: AsyncClient):
    """Test that health check responds quickly."""
    import time

    start = time.time()
    response = await api_client.get("/health")
    duration = time.time() - start

    assert response.status_code == 200
    # Health check should be fast (<1 second)
    assert duration < 1.0


@pytest.mark.asyncio
async def test_health_check_version_format(api_client: AsyncClient):
    """Test that health check includes version in correct format."""
    response = await api_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "version" in data
    # Version should be a non-empty string
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0


@pytest.mark.asyncio
async def test_health_check_timestamp_format(api_client: AsyncClient):
    """Test that health check includes ISO timestamp."""
    response = await api_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "timestamp" in data
    # Should be ISO format timestamp
    assert isinstance(data["timestamp"], str)
    assert "T" in data["timestamp"]  # ISO format includes T separator


@pytest.mark.asyncio
async def test_health_check_headers(api_client: AsyncClient):
    """Test that health check includes proper response headers."""
    response = await api_client.get("/health")

    assert "content-type" in response.headers
    assert "application/json" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_readiness_probe_structure(api_client: AsyncClient):
    """Test readiness probe response structure."""
    response = await api_client.get("/health/ready")

    data = response.json()
    assert "status" in data

    # Optionally may include checks
    if "checks" in data:
        assert isinstance(data["checks"], dict)


@pytest.mark.asyncio
async def test_liveness_probe_minimal_response(api_client: AsyncClient):
    """Test that liveness probe has minimal overhead."""
    response = await api_client.get("/health/live")

    assert response.status_code == 200
    data = response.json()

    # Liveness should be very lightweight
    assert "status" in data
    # Should not include heavy checks
    assert "checks" not in data or len(data.get("checks", {})) == 0
