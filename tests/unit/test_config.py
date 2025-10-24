"""Test configuration management."""

from aetherlens.config import Settings


def test_settings_loads_defaults():
    """Test that settings load with default values."""
    settings = Settings(
        database_url="postgresql://test:test@localhost/test",
        secret_key="test_key_minimum_32_characters_long!",
    )
    assert settings.aetherlens_log_level == "info"
    assert settings.jwt_algorithm == "HS256"
    assert settings.database_pool_size == 10


def test_settings_accepts_custom_values():
    """Test that settings accept custom values."""
    settings = Settings(
        database_url="postgresql://test:test@localhost/test",
        secret_key="test_key_minimum_32_characters_long!",
        aetherlens_log_level="debug",
        database_pool_size=20,
    )
    assert settings.aetherlens_log_level == "debug"
    assert settings.database_pool_size == 20


def test_settings_has_required_fields():
    """Test that settings has all required configuration fields."""
    settings = Settings(
        database_url="postgresql://test:test@localhost/test",
        secret_key="test_key_minimum_32_characters_long!",
    )
    # Core settings
    assert hasattr(settings, "aetherlens_home")
    assert hasattr(settings, "database_url")
    assert hasattr(settings, "secret_key")

    # Security settings
    assert hasattr(settings, "jwt_algorithm")
    assert hasattr(settings, "jwt_access_token_expire_minutes")

    # Optional settings
    assert hasattr(settings, "redis_url")
    assert hasattr(settings, "prometheus_enabled")
