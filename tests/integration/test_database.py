"""
Database integration tests.

Tests for:
- Database connectivity
- Basic CRUD operations
- TimescaleDB hypertables
- Continuous aggregates
- Indexes and performance
- Transaction handling
"""

import pytest
from datetime import datetime, timedelta


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_connection(db_pool):
    """Test basic database connectivity."""
    async with db_pool.acquire() as conn:
        result = await conn.fetchval("SELECT 1")
        assert result == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_timescaledb_extension(db_pool):
    """Test that TimescaleDB extension is installed and active."""
    async with db_pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM pg_extension WHERE extname = 'timescaledb'"
        )
        assert result == 1, "TimescaleDB extension not installed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_version(db_pool):
    """Test PostgreSQL version is compatible."""
    async with db_pool.acquire() as conn:
        version = await conn.fetchval("SELECT version()")
        assert "PostgreSQL" in version
        # Should be PostgreSQL 15
        assert "15" in version


@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_tables_exist(db_pool):
    """Test that all expected tables exist."""
    expected_tables = [
        "devices",
        "users",
        "api_tokens",
        "rate_schedules",
        "alerts",
        "plugins",
        "migration_history",
        "metrics",
        "cost_calculations",
    ]

    async with db_pool.acquire() as conn:
        for table in expected_tables:
            exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = $1
                )
                """,
                table,
            )
            assert exists, f"Table '{table}' does not exist"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_insert_and_query_device(db_pool):
    """Test inserting and querying a device."""
    device_id = f"integration-test-device-{datetime.utcnow().timestamp()}"

    async with db_pool.acquire() as conn:
        # Insert device
        await conn.execute(
            """
            INSERT INTO devices (device_id, name, type, manufacturer, model)
            VALUES ($1, $2, $3, $4, $5)
            """,
            device_id,
            "Integration Test Device",
            "smart_plug",
            "Test Corp",
            "IT-100",
        )

        # Query device
        result = await conn.fetchrow(
            "SELECT * FROM devices WHERE device_id = $1", device_id
        )

        assert result is not None
        assert result["device_id"] == device_id
        assert result["name"] == "Integration Test Device"
        assert result["type"] == "smart_plug"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_insert_and_query_metrics(db_pool, sample_device):
    """Test inserting and querying time-series metrics."""
    async with db_pool.acquire() as conn:
        # Insert metric
        now = datetime.utcnow()
        await conn.execute(
            """
            INSERT INTO metrics (device_id, time, metric_type, value, unit)
            VALUES ($1, $2, $3, $4, $5)
            """,
            sample_device["device_id"],
            now,
            "power",
            125.5,
            "watts",
        )

        # Query metric
        result = await conn.fetchrow(
            """
            SELECT * FROM metrics
            WHERE device_id = $1 AND time = $2
            """,
            sample_device["device_id"],
            now,
        )

        assert result is not None
        assert result["value"] == 125.5
        assert result["unit"] == "watts"
        assert result["metric_type"] == "power"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hypertable_chunks(db_pool, sample_metrics):
    """Test that hypertable is creating chunks."""
    async with db_pool.acquire() as conn:
        chunks = await conn.fetch(
            """
            SELECT chunk_schema, chunk_name
            FROM timescaledb_information.chunks
            WHERE hypertable_name = 'metrics'
            """
        )

        # Should have at least one chunk
        assert len(chunks) > 0, "Hypertable has no chunks"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_continuous_aggregates_exist(db_pool):
    """Test that continuous aggregates are created."""
    expected_aggregates = [
        "metrics_hourly",
        "metrics_daily",
        "cost_hourly",
        "cost_daily",
    ]

    async with db_pool.acquire() as conn:
        for aggregate in expected_aggregates:
            exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = $1
                )
                """,
                aggregate,
            )
            assert exists, f"Continuous aggregate '{aggregate}' does not exist"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_continuous_aggregate_refresh(db_pool, sample_metrics):
    """Test that continuous aggregates can be refreshed."""
    async with db_pool.acquire() as conn:
        # Manually refresh aggregate
        await conn.execute(
            "CALL refresh_continuous_aggregate('metrics_hourly', NULL, NULL)"
        )

        # Query aggregate
        result = await conn.fetch(
            "SELECT * FROM metrics_hourly ORDER BY bucket DESC LIMIT 1"
        )

        assert len(result) > 0, "Continuous aggregate has no data"
        # Verify structure
        row = dict(result[0])
        assert "bucket" in row
        assert "device_id" in row
        assert "avg_value" in row


@pytest.mark.integration
@pytest.mark.asyncio
async def test_device_metrics_foreign_key(db_pool, sample_device, sample_metrics):
    """Test foreign key relationship between devices and metrics."""
    async with db_pool.acquire() as conn:
        # Query metrics with device join
        result = await conn.fetch(
            """
            SELECT m.*, d.name as device_name
            FROM metrics m
            JOIN devices d ON m.device_id = d.device_id
            WHERE m.device_id = $1
            LIMIT 10
            """,
            sample_device["device_id"],
        )

        assert len(result) > 0, "No metrics found for device"
        # All should have the device name
        assert all(
            r["device_name"] == sample_device["name"] for r in result
        ), "Device join failed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_transaction_rollback(db_pool, sample_device):
    """Test that transaction rollback works correctly."""
    async with db_pool.acquire() as conn:
        # Start transaction
        async with conn.transaction():
            # Update device name
            await conn.execute(
                "UPDATE devices SET name = 'Modified Name' WHERE device_id = $1",
                sample_device["device_id"],
            )

            # Verify change within transaction
            result = await conn.fetchval(
                "SELECT name FROM devices WHERE device_id = $1",
                sample_device["device_id"],
            )
            assert result == "Modified Name"

            # Rollback by raising exception
            raise Exception("Force rollback")

    # Verify rollback happened
    async with db_pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT name FROM devices WHERE device_id = $1", sample_device["device_id"]
        )
        # Should still have original name
        assert result == sample_device["name"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_indexes_exist(db_pool):
    """Test that critical indexes exist."""
    critical_indexes = [
        "idx_metrics_device_time",
        "idx_devices_type",
        "idx_users_username",
    ]

    async with db_pool.acquire() as conn:
        for index in critical_indexes:
            exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE indexname = $1
                )
                """,
                index,
            )
            assert exists, f"Index '{index}' does not exist"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_performance_with_index(db_pool, sample_metrics):
    """Test that queries using indexes are fast."""
    import time

    async with db_pool.acquire() as conn:
        start = time.time()

        # Query that should use idx_metrics_device_time index
        result = await conn.fetch(
            """
            SELECT * FROM metrics
            WHERE device_id = $1
            AND time > NOW() - INTERVAL '1 hour'
            ORDER BY time DESC
            LIMIT 100
            """,
            sample_metrics[0]["device_id"],
        )

        duration = time.time() - start

        # Should be very fast (<100ms)
        assert duration < 0.1, f"Query took {duration:.3f}s (expected <0.1s)"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_batch_insert_performance(db_pool, sample_device):
    """Test batch insert performance."""
    import time

    metrics = []
    base_time = datetime.utcnow()

    # Generate 100 metrics
    for i in range(100):
        metrics.append(
            (
                sample_device["device_id"],
                base_time + timedelta(seconds=i),
                "power",
                100.0 + i,
                "watts",
            )
        )

    async with db_pool.acquire() as conn:
        start = time.time()

        await conn.executemany(
            """
            INSERT INTO metrics (device_id, time, metric_type, value, unit)
            VALUES ($1, $2, $3, $4, $5)
            """,
            metrics,
        )

        duration = time.time() - start

        # 100 inserts should be fast (<1 second)
        assert duration < 1.0, f"Batch insert took {duration:.3f}s (expected <1s)"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_password_hash_storage(db_pool):
    """Test that passwords are stored as hashes."""
    from aetherlens.security.passwords import hash_password

    user_id = f"test-password-user-{datetime.utcnow().timestamp()}"
    password_hash = hash_password("test_password_123")

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, username, email, password_hash, role)
            VALUES ($1, $2, $3, $4, $5)
            """,
            user_id,
            "testpassuser",
            "testpass@example.com",
            password_hash,
            "user",
        )

        # Query password hash
        stored_hash = await conn.fetchval(
            "SELECT password_hash FROM users WHERE user_id = $1", user_id
        )

        # Should be a bcrypt hash
        assert stored_hash.startswith("$2"), "Password hash not in bcrypt format"
        # Should not be the plaintext password
        assert stored_hash != "test_password_123"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jsonb_configuration_storage(db_pool):
    """Test storing JSON configuration in JSONB field."""
    device_id = f"test-jsonb-device-{datetime.utcnow().timestamp()}"
    configuration = {
        "ip": "192.168.1.50",
        "poll_interval": 30,
        "features": ["power", "energy", "voltage"],
    }

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO devices (device_id, name, type, configuration)
            VALUES ($1, $2, $3, $4)
            """,
            device_id,
            "JSON Test Device",
            "smart_plug",
            configuration,
        )

        # Query configuration
        result = await conn.fetchval(
            "SELECT configuration FROM devices WHERE device_id = $1", device_id
        )

        # Should retrieve as dict
        assert isinstance(result, dict)
        assert result["ip"] == "192.168.1.50"
        assert result["poll_interval"] == 30
        assert result["features"] == ["power", "energy", "voltage"]
