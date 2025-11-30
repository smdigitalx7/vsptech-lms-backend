from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
from app.core.config import (
    settings,
    DB_HEALTH_CHECK_QUERY,
    DB_HEALTH_CHECK_RETRY_ATTEMPTS,
    DB_HEALTH_CHECK_RETRY_DELAY_SECONDS,
)
from app.core.logger import get_logger

logger = get_logger(__name__)


# Database Configuration
DATABASE_URL = settings.postgres_url

# Create async engine with configurable pool settings from environment
async_engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,
    future=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database session.

    Yields:
        AsyncSession: Database session with proper lifecycle management

    Automatically commits on successful completion and rolls back on exception.
    Services/repositories should use flush() to get auto-generated IDs before commit.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Commit transaction on successful completion
            await session.commit()
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_health() -> bool:
    """
    Check database connectivity with retry logic.

    Returns:
        bool: True if database is accessible, False otherwise
    """
    import asyncio

    for attempt in range(DB_HEALTH_CHECK_RETRY_ATTEMPTS):
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text(DB_HEALTH_CHECK_QUERY))
            logger.info(f"Database health check successful on attempt {attempt + 1}")
            return True
        except Exception as e:
            logger.error(f"Database health check failed on attempt {attempt + 1}: {e}")
            if attempt < DB_HEALTH_CHECK_RETRY_ATTEMPTS - 1:  # Don't sleep on the last attempt
                await asyncio.sleep(DB_HEALTH_CHECK_RETRY_DELAY_SECONDS)
    return False

