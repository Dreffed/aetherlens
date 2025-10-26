"""
Database migration tests.

Tests for:
- Migration execution
- Schema verification
- Index creation
- Constraint validation
"""

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_migration_history_table_exists(db_pool):
    """Test that migration history table exists."""
    async with db_pool.acquire() as conn:
        exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'migration_history'
            )
            """
        )
        assert exists, "migration_history table does not exist"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_devices_table_schema(db_pool):
    """Test devices table has correct schema."""
    async with db_pool.acquire() as conn:
        columns = await conn.fetch(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'devices'
            ORDER BY ordinal_position
            """
        )

        column_names = [col["column_name"] for col in columns]

        # Verify required columns exist
        required_columns = ["device_id", "name", "type", "created_at", "updated_at"]
        for col in required_columns:
            assert col in column_names, f"Required column '{col}' missing from devices table"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_users_table_schema(db_pool):
    """Test users table has correct schema."""
    async with db_pool.acquire() as conn:
        columns = await conn.fetch(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
            """
        )

        column_names = [col["column_name"] for col in columns]

        required_columns = ["user_id", "username", "email", "password_hash", "role"]
        for col in required_columns:
            assert col in column_names, f"Required column '{col}' missing from users table"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_is_hypertable(db_pool):
    """Test that metrics table is a TimescaleDB hypertable."""
    async with db_pool.acquire() as conn:
        is_hypertable = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM timescaledb_information.hypertables
                WHERE hypertable_name = 'metrics'
            )
            """
        )
        assert is_hypertable, "metrics table is not a hypertable"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cost_calculations_is_hypertable(db_pool):
    """Test that cost_calculations table is a hypertable."""
    async with db_pool.acquire() as conn:
        is_hypertable = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM timescaledb_information.hypertables
                WHERE hypertable_name = 'cost_calculations'
            )
            """
        )
        assert is_hypertable, "cost_calculations table is not a hypertable"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_primary_keys_exist(db_pool):
    """Test that all tables have primary keys."""
    tables = ["devices", "users", "rate_schedules", "alerts", "plugins"]

    async with db_pool.acquire() as conn:
        for table in tables:
            has_pk = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.table_constraints
                    WHERE table_name = $1
                    AND constraint_type = 'PRIMARY KEY'
                )
                """,
                table,
            )
            assert has_pk, f"Table '{table}' has no primary key"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_foreign_key_constraints(db_pool):
    """Test that foreign key constraints exist."""
    async with db_pool.acquire() as conn:
        # metrics should reference devices
        fk_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage ccu
                  ON tc.constraint_name = ccu.constraint_name
                WHERE tc.table_name = 'metrics'
                AND tc.constraint_type = 'FOREIGN KEY'
                AND ccu.table_name = 'devices'
            )
            """
        )
        assert fk_exists, "Foreign key from metrics to devices does not exist"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unique_constraints(db_pool):
    """Test that unique constraints are properly defined."""
    async with db_pool.acquire() as conn:
        # Users table should have unique username
        unique_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.table_constraints
                WHERE table_name = 'users'
                AND constraint_type = 'UNIQUE'
                AND constraint_name LIKE '%username%'
            )
            """
        )
        assert unique_exists or await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM pg_indexes
                WHERE tablename = 'users'
                AND indexdef LIKE '%UNIQUE%'
                AND indexdef LIKE '%username%'
            )
            """
        ), "Unique constraint on username does not exist"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_not_null_constraints(db_pool):
    """Test that NOT NULL constraints are properly set."""
    async with db_pool.acquire() as conn:
        # Check critical NOT NULL columns
        result = await conn.fetchrow(
            """
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_name = 'devices'
            AND column_name = 'device_id'
            """
        )
        assert result["is_nullable"] == "NO", "device_id should be NOT NULL"

        result = await conn.fetchrow(
            """
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            AND column_name = 'username'
            """
        )
        assert result["is_nullable"] == "NO", "username should be NOT NULL"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_timestamp_defaults(db_pool):
    """Test that timestamp columns have defaults."""
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT column_default
            FROM information_schema.columns
            WHERE table_name = 'devices'
            AND column_name = 'created_at'
            """
        )
        # Should have a default (likely NOW() or CURRENT_TIMESTAMP)
        assert result["column_default"] is not None, "created_at should have default"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_compression_policy_exists(db_pool):
    """Test that compression policy exists for metrics."""
    async with db_pool.acquire() as conn:
        policies = await conn.fetch(
            """
            SELECT * FROM timescaledb_information.compression_settings
            WHERE hypertable_name = 'metrics'
            """
        )
        # Should have compression configured
        assert len(policies) > 0, "No compression policy found for metrics"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_retention_policy_exists(db_pool):
    """Test that retention policies are configured."""
    async with db_pool.acquire() as conn:
        policies = await conn.fetch(
            """
            SELECT * FROM timescaledb_information.jobs
            WHERE proc_name = 'policy_retention'
            """
        )
        # Should have at least one retention policy
        assert len(policies) > 0, "No retention policies found"
