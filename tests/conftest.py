"""
Pytest configuration and fixtures for AetherLens tests.

This module provides comprehensive test fixtures for:
- Database connections and transactions
- API clients (authenticated and unauthenticated)
- Test users (regular and admin)
- Sample data (devices, metrics, rate schedules)
"""

import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, List

import asyncpg
import pytest
from httpx import AsyncClient

from aetherlens.api.database import db_manager
from aetherlens.api.main import create_app
from aetherlens.config import Settings, settings
from aetherlens.security.jwt import jwt_manager
from aetherlens.security.passwords import hash_password


# ============================================================================
# Event Loop Configuration
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    Test configuration settings.

    Returns test-specific database URL and settings.
    Uses port 5433 to avoid conflicts with dev database.
    """
    return Settings(
        database_url="postgresql://postgres:test_password@localhost:5433/aetherlens_test",
        redis_url="redis://localhost:6380/0",
        secret_key="test_secret_key_minimum_32_characters_long_for_testing_only",
        aetherlens_log_level="debug",
        debug=True,
    )


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture(scope="session")
async def db_pool(test_settings) -> AsyncGenerator[asyncpg.Pool, None]:
    """
    Create database connection pool for tests.

    This fixture creates a connection pool that is reused across
    all tests in the session for performance.
    """
    pool = await asyncpg.create_pool(
        test_settings.database_url,
        min_size=5,
        max_size=10,
    )
    yield pool
    await pool.close()


@pytest.fixture
async def db_transaction(db_pool):
    """
    Wrap each test in a transaction and rollback after.

    This provides test isolation - each test gets a clean database state.
    All changes are automatically rolled back at the end of the test.
    """
    async with db_pool.acquire() as conn:
        transaction = conn.transaction()
        await transaction.start()
        try:
            yield conn
        finally:
            await transaction.rollback()


@pytest.fixture
async def db_conn(db_pool) -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Provide a database connection for tests that need direct access.

    Note: This doesn't auto-rollback. Use db_transaction for isolation.
    """
    async with db_pool.acquire() as conn:
        yield conn


# ============================================================================
# User Fixtures
# ============================================================================


@pytest.fixture
async def test_user(db_pool) -> Dict:
    """
    Create a test user with regular permissions.

    Returns user data without password hash for convenience.
    """
    user_id = f"test-user-{datetime.utcnow().timestamp()}"
    user_data = {
        "user_id": user_id,
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": hash_password("testpassword123"),
        "role": "user",
    }

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, username, email, password_hash, role)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_data["user_id"],
            user_data["username"],
            user_data["email"],
            user_data["password_hash"],
            user_data["role"],
        )

    # Return without password hash
    return {k: v for k, v in user_data.items() if k != "password_hash"}


@pytest.fixture
async def admin_user(db_pool) -> Dict:
    """
    Create an admin user with full permissions.

    Returns user data without password hash for convenience.
    """
    user_id = f"admin-user-{datetime.utcnow().timestamp()}"
    user_data = {
        "user_id": user_id,
        "username": "adminuser",
        "email": "admin@example.com",
        "password_hash": hash_password("adminpassword123"),
        "role": "admin",
    }

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, username, email, password_hash, role)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_data["user_id"],
            user_data["username"],
            user_data["email"],
            user_data["password_hash"],
            user_data["role"],
        )

    return {k: v for k, v in user_data.items() if k != "password_hash"}


# ============================================================================
# Authentication Fixtures
# ============================================================================


@pytest.fixture
def user_token(test_user) -> str:
    """
    Generate JWT token for test user.

    Returns a valid access token for API authentication.
    """
    token_data = {
        "sub": test_user["user_id"],
        "username": test_user["username"],
        "role": test_user["role"],
    }
    return jwt_manager.create_access_token(token_data)


@pytest.fixture
def admin_token(admin_user) -> str:
    """
    Generate JWT token for admin user.

    Returns a valid access token for API authentication with admin privileges.
    """
    token_data = {
        "sub": admin_user["user_id"],
        "username": admin_user["username"],
        "role": admin_user["role"],
    }
    return jwt_manager.create_access_token(token_data)


# ============================================================================
# API Client Fixtures
# ============================================================================


@pytest.fixture
async def api_client(test_settings) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for API testing.

    Provides an unauthenticated client for testing public endpoints
    and authentication flows.
    """
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def authenticated_client(api_client, user_token) -> AsyncClient:
    """
    Create authenticated API client with user token.

    Use this for testing endpoints that require authentication
    with regular user permissions.
    """
    api_client.headers.update({"Authorization": f"Bearer {user_token}"})
    return api_client


@pytest.fixture
async def admin_client(api_client, admin_token) -> AsyncClient:
    """
    Create authenticated API client with admin token.

    Use this for testing endpoints that require admin permissions.
    """
    api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return api_client


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
async def sample_device(db_pool, admin_user) -> Dict:
    """
    Create a sample device for testing.

    Returns device data as a dictionary.
    """
    device_id = f"test-device-{datetime.utcnow().timestamp()}"
    device_data = {
        "device_id": device_id,
        "name": "Test Smart Plug",
        "type": "smart_plug",
        "manufacturer": "Test Corp",
        "model": "TP-100",
        "configuration": {"ip": "192.168.1.100", "poll_interval": 30},
    }

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO devices (device_id, name, type, manufacturer, model, configuration)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (device_id) DO NOTHING
            """,
            device_data["device_id"],
            device_data["name"],
            device_data["type"],
            device_data["manufacturer"],
            device_data["model"],
            device_data["configuration"],
        )

    return device_data


@pytest.fixture
async def sample_devices(db_pool, admin_user) -> List[Dict]:
    """
    Create multiple sample devices for testing.

    Returns list of device data dictionaries.
    """
    devices = []
    device_types = ["smart_plug", "energy_monitor", "solar_inverter"]

    for i, device_type in enumerate(device_types):
        device_id = f"test-device-{device_type}-{datetime.utcnow().timestamp()}-{i}"
        device_data = {
            "device_id": device_id,
            "name": f"Test {device_type.replace('_', ' ').title()} {i+1}",
            "type": device_type,
            "manufacturer": "Test Corp",
            "model": f"Model-{i+1}",
            "configuration": {"ip": f"192.168.1.{100+i}"},
        }

        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO devices (device_id, name, type, manufacturer, model, configuration)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (device_id) DO NOTHING
                """,
                device_data["device_id"],
                device_data["name"],
                device_data["type"],
                device_data["manufacturer"],
                device_data["model"],
                device_data["configuration"],
            )

        devices.append(device_data)

    return devices


@pytest.fixture
async def sample_metrics(db_pool, sample_device) -> List[Dict]:
    """
    Create sample time-series metrics for testing.

    Generates 24 hours of metrics at 5-minute intervals (288 data points).
    Returns list of metric dictionaries.
    """
    metrics = []
    base_time = datetime.utcnow() - timedelta(hours=24)

    # Generate 288 metrics (24 hours * 12 per hour)
    for i in range(288):
        timestamp = base_time + timedelta(minutes=5 * i)
        # Vary power consumption realistically (80-150 watts with some pattern)
        hour = timestamp.hour
        base_power = 100
        # Higher during day, lower at night
        if 6 <= hour < 22:
            base_power = 120
        else:
            base_power = 80

        # Add some variation
        power = base_power + (i % 30) - 15

        metric = {
            "device_id": sample_device["device_id"],
            "time": timestamp,
            "metric_type": "power",
            "value": float(power),
            "unit": "watts",
        }
        metrics.append(metric)

    # Batch insert for performance
    async with db_pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO metrics (device_id, time, metric_type, value, unit)
            VALUES ($1, $2, $3, $4, $5)
            """,
            [
                (
                    m["device_id"],
                    m["time"],
                    m["metric_type"],
                    m["value"],
                    m["unit"],
                )
                for m in metrics
            ],
        )

    return metrics


@pytest.fixture
async def sample_rate_schedule(db_pool) -> Dict:
    """
    Create a sample electricity rate schedule for testing.

    Returns rate schedule data as a dictionary.
    """
    schedule_id = f"test-schedule-{datetime.utcnow().timestamp()}"
    schedule_data = {
        "rate_schedule_id": schedule_id,
        "name": "Test Time-of-Use Schedule",
        "provider": "Test Utility Company",
        "currency": "USD",
        "rate_type": "time_of_use",
        "rates": {
            "peak": 0.42,
            "off_peak": 0.24,
            "super_off_peak": 0.12,
        },
        "schedule": {
            "peak_hours": "16:00-21:00",
            "peak_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
        },
    }

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO rate_schedules (rate_schedule_id, name, provider, currency, rate_type, rates, schedule)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (rate_schedule_id) DO NOTHING
            """,
            schedule_data["rate_schedule_id"],
            schedule_data["name"],
            schedule_data["provider"],
            schedule_data["currency"],
            schedule_data["rate_type"],
            schedule_data["rates"],
            schedule_data["schedule"],
        )

    return schedule_data


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """
    Configure pytest with custom markers.

    This allows tests to be categorized and run selectively.
    """
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires services)"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance benchmark"
    )
    config.addinivalue_line("markers", "security: mark test as security scan")
    config.addinivalue_line("markers", "quality: mark test as code quality check")
    config.addinivalue_line("markers", "slow: mark test as slow-running")
