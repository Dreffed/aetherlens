"""
Database connection management for FastAPI.
"""

import asyncpg
import structlog

from aetherlens.config import settings

logger = structlog.get_logger()


class DatabaseManager:
    """Manages PostgreSQL connection pool."""

    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Create database connection pool."""
        if self.pool is not None:
            logger.warning("Database pool already exists")
            return

        self.pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=settings.database_pool_size,
            max_size=settings.database_pool_size + settings.database_max_overflow,
            command_timeout=60,
        )
        logger.info("Database pool created")

    async def disconnect(self) -> None:
        """Close database connection pool."""
        if self.pool is None:
            logger.warning("No database pool to close")
            return

        await self.pool.close()
        self.pool = None
        logger.info("Database pool closed")

    def get_pool(self) -> asyncpg.Pool:
        """Get database connection pool."""
        if self.pool is None:
            raise RuntimeError("Database pool not initialized")
        return self.pool


db_manager = DatabaseManager()
