from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any, AsyncContextManager
import anyio
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, FastAPI
from app.core.config import settings, DEFAULT_THREAD_POOL_TOKENS
from app.core.database import async_engine as engine
from app.core.database import check_database_health
from app.core.utils import cache, queue
from app.core.logger import get_app_logger, get_error_logger, get_database_logger

logger = get_app_logger(__name__)
error_logger = get_error_logger(__name__)
db_logger = get_database_logger(__name__)


# ------------------ Redis Cache ------------------
async def create_redis_cache_pool() -> None:
    """Initialize Redis cache connection."""
    success = await cache.cache_manager.connect(settings.redis_cache_url)
    if success:
        logger.info("Redis cache pool created successfully")
    else:
        logger.warning("Failed to create Redis cache pool")


async def close_redis_cache_pool() -> None:
    """Close Redis cache connection."""
    await cache.cache_manager.disconnect()


# ------------------ Redis Queue ------------------
async def create_redis_queue_pool() -> None:
    """Initialize Redis queue connection."""
    try:
        queue.pool = await create_pool(
            RedisSettings(host=settings.redis_queue_host, port=settings.redis_queue_port)
        )
        logger.info("Redis queue pool created successfully")
    except Exception as e:
        logger.error(f"Failed to create Redis queue pool: {e}")


async def close_redis_queue_pool() -> None:
    """Close Redis queue connection."""
    if queue.pool is not None:
        await queue.pool.aclose()
        logger.info("Redis queue pool closed")


# ------------------ Thread Pool Tokens ------------------
async def set_threadpool_tokens(number_of_tokens: int = DEFAULT_THREAD_POOL_TOKENS) -> None:
    """
    Set the default thread pool limiter for the app.
    """
    try:
        limiter = anyio.CapacityLimiter(number_of_tokens)
        setattr(anyio.to_thread, 'current_default_thread_limiter', limiter)
    except AttributeError:
        try:
            limiter = getattr(anyio.to_thread, 'current_default_thread_limiter', None)
            if limiter is not None:
                limiter.total_tokens = number_of_tokens
        except Exception as e:
            logger.warning(f"Failed to set thread pool limiter: {e}")


# ------------------ Lifespan Factory ------------------
def lifespan_factory() -> Callable[[FastAPI], AsyncContextManager[None]]:
    """
    Factory to create a lifespan context manager for FastAPI app.
    No automatic table creation. Alembic is mandatory.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from asyncio import Event

        initialization_complete = Event()
        app.state.initialization_complete = initialization_complete

        # Set thread pool tokens from settings
        await set_threadpool_tokens(getattr(settings, 'thread_pool_tokens', DEFAULT_THREAD_POOL_TOKENS))

        try:
            # Initialize Redis cache
            await create_redis_cache_pool()

            # Initialize Redis queue
            await create_redis_queue_pool()

            # Optional DB connectivity check (non-fatal)
            try:
                db_ok = await check_database_health()
                if not db_ok:
                    db_logger.warning("Database health check failed during startup")
                    error_logger.error("Database connectivity issue detected")
                else:
                    db_logger.info("Database health check passed")
            except Exception as e:
                db_logger.error(f"Database health check error during startup: {e}")
                error_logger.error(f"Database health check failed: {e}")

            initialization_complete.set()
            yield

        finally:
            # Cleanup Redis pools
            await close_redis_cache_pool()
            await close_redis_queue_pool()

            # Dispose SQLAlchemy engine
            await engine.dispose()

            # Stop async logging listener
            try:
                from app.core.logger import stop_async_logging
                stop_async_logging()
            except Exception:
                pass  # Ignore errors during shutdown

    return lifespan


# ------------------ FastAPI App Factory ------------------
def create_application(
    router: APIRouter,
    lifespan: Callable[[FastAPI], AsyncContextManager[None]] | None = None,
    **kwargs: Any,
) -> FastAPI:
    """
    Create and configure a FastAPI app based on provided settings.
    """

    # App metadata
    kwargs.update({
        "title": settings.app_name,
        "description": settings.app_description,
    })

    # Enable Swagger UI & Redoc only in non-production
    if settings.environment.value != "production":
        kwargs.update({
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "openapi_url": "/openapi.json",
        })
    else:
        kwargs.update({
            "docs_url": None,
            "redoc_url": None,
            "openapi_url": None,
        })

    # Use provided lifespan or default one
    if lifespan is None:
        lifespan = lifespan_factory()

    # Initialize app
    application = FastAPI(lifespan=lifespan, **kwargs)

    # Include routers
    application.include_router(router)

    return application

