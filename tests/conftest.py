"""
Pytest configuration and fixtures for AetherLens tests.
"""

import pytest


@pytest.fixture
def test_settings():
    """Test configuration settings."""
    from aetherlens.config import Settings

    return Settings(
        database_url="postgresql://postgres:test@localhost:5432/aetherlens_test",
        redis_url=None,  # Use in-memory for tests
        secret_key="test_secret_key_for_testing_only",
        debug=True,
    )


@pytest.fixture
def client(test_settings):
    """Test client for API testing."""
    # Will be implemented when we create the FastAPI app
    pass
