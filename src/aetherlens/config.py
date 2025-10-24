"""
Configuration management for AetherLens.
"""

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core
    aetherlens_home: str = "/opt/aetherlens"
    aetherlens_log_level: str = "info"
    aetherlens_bind_addr: str = "0.0.0.0:8080"

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql://postgres:changeme@localhost:5432/aetherlens"
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Security
    secret_key: str = Field(
        default="INSECURE_DEFAULT_KEY_CHANGE_ME",
        min_length=32,
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # Redis (optional)
    redis_url: RedisDsn | None = Field(default=None)
    redis_max_connections: int = 50

    # Plugins
    plugin_path: str = "/opt/aetherlens/plugins"
    plugin_timeout_seconds: int = 30
    plugin_max_memory_mb: int = 256

    # Monitoring
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    log_format: str = "json"

    # Development
    debug: bool = False
    reload: bool = False


# Global settings instance
settings = Settings()
