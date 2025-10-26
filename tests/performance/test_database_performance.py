"""Database query performance tests."""

import time

import pytest


@pytest.mark.performance
@pytest.mark.asyncio
async def test_recent_metrics_query_performance(db_pool, sample_metrics):
    """Test performance of recent metrics query."""
    async with db_pool.acquire() as conn:
        times = []

        for _ in range(10):
            start = time.time()
            result = await conn.fetch(
                """
                SELECT * FROM metrics
                WHERE time > NOW() - INTERVAL '24 hours'
                ORDER BY time DESC
                LIMIT 100
                """
            )
            duration = time.time() - start
            times.append(duration)
            assert len(result) >= 0

        avg_time = sum(times) / len(times)
        assert avg_time < 0.05, f"Average query time {avg_time:.3f}s > 50ms"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_aggregate_query_performance(db_pool, sample_metrics):
    """Test performance of aggregate queries."""
    async with db_pool.acquire() as conn:
        start = time.time()
        _ = await conn.fetchrow(
            """
            SELECT
                device_id,
                AVG(value) as avg_power,
                MAX(value) as max_power,
                MIN(value) as min_power
            FROM metrics
            WHERE time > NOW() - INTERVAL '7 days'
            GROUP BY device_id
            """
        )
        duration = time.time() - start

        assert duration < 0.5, f"Aggregate query took {duration:.3f}s > 500ms"
