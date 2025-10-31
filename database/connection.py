"""
Async database connection manager using SQLAlchemy 2.0 and AsyncPG
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from contextlib import asynccontextmanager
import os
import logging
from typing import Optional, AsyncGenerator

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages async database connections and sessions"""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the database manager.

        Args:
            database_url: Database connection URL. If None, loads from DATABASE_URL environment variable.
        """
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql+asyncpg://arbitrage_user:arbitrage_secure_password@localhost:5432/arbitrage_bot",
            )

        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self.is_initialized = False

    async def initialize(self) -> None:
        """Initialize database engine and test connection"""
        try:
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
            )

            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )

            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))

            self.is_initialized = True
            logger.info("✓ Database initialized successfully")

        except Exception as e:
            logger.error(f"✗ Failed to initialize database: {e}")
            raise

    async def create_tables(self) -> None:
        """Create all tables from models"""
        if not self.engine:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✓ Database tables created successfully")
        except Exception as e:
            logger.error(f"✗ Failed to create tables: {e}")
            raise

    async def setup_timescale_hypertables(self) -> None:
        """Setup TimescaleDB hypertables for time-series tables"""
        if not self.engine:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        hypertable_queries = [
            "SELECT create_hypertable('stats_snapshots', 'timestamp', if_not_exists => TRUE);",
            "SELECT create_hypertable('gas_prices', 'timestamp', if_not_exists => TRUE);",
            "SELECT create_hypertable('chain_metrics', 'timestamp', if_not_exists => TRUE);",
            "SELECT add_retention_policy('stats_snapshots', INTERVAL '90 days', if_not_exists => TRUE);",
            "SELECT add_retention_policy('gas_prices', INTERVAL '30 days', if_not_exists => TRUE);",
            "SELECT add_retention_policy('chain_metrics', INTERVAL '7 days', if_not_exists => TRUE);",
        ]

        try:
            async with self.engine.begin() as conn:
                for query in hypertable_queries:
                    try:
                        await conn.execute(__import__("sqlalchemy").text(query))
                        logger.debug(f"Executed: {query[:50]}...")
                    except Exception as e:
                        logger.warning(
                            f"Hypertable query failed (may already exist): {e}"
                        )

            logger.info("✓ TimescaleDB hypertables configured")
        except Exception as e:
            logger.error(f"✗ Failed to setup TimescaleDB hypertables: {e}")
            raise

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a new async database session.

        Usage:
            async with db_manager.get_session() as session:
                result = await session.execute(query)
                await session.commit()
        """
        if not self.session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

    async def close(self) -> None:
        """Close database engine and cleanup resources"""
        if self.engine:
            await self.engine.dispose()
            logger.info("✓ Database connections closed")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get or create global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for getting database session"""
    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        yield session
