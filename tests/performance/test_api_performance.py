"""API endpoint performance tests."""

import asyncio
import time

import pytest
from httpx import AsyncClient


@pytest.mark.performance
@pytest.mark.asyncio
async def test_health_check_performance(api_client: AsyncClient):
    """Test health check response time."""
    times = []

    for _ in range(10):
        start = time.time()
        response = await api_client.get("/health")
        duration = time.time() - start
        times.append(duration)
        assert response.status_code == 200

    avg_time = sum(times) / len(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]

    assert avg_time < 0.1, f"Average response time {avg_time:.3f}s > 100ms"
    assert p95_time < 0.2, f"P95 response time {p95_time:.3f}s > 200ms"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_device_list_performance(authenticated_client: AsyncClient, sample_devices):
    """Test device list endpoint performance."""
    times = []

    for _ in range(10):
        start = time.time()
        response = await authenticated_client.get("/api/v1/devices")
        duration = time.time() - start
        times.append(duration)
        assert response.status_code == 200

    avg_time = sum(times) / len(times)
    assert avg_time < 0.2, f"Average response time {avg_time:.3f}s > 200ms"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_requests(authenticated_client: AsyncClient):
    """Test handling concurrent requests."""

    async def make_request():
        return await authenticated_client.get("/health/live")

    start = time.time()
    tasks = [make_request() for _ in range(50)]
    responses = await asyncio.gather(*tasks)
    duration = time.time() - start

    assert all(r.status_code == 200 for r in responses)
    assert duration < 5.0, f"50 concurrent requests took {duration:.2f}s > 5s"
