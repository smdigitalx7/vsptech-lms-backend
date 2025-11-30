from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any, AsyncContextManager
import asyncio
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
        from app.core.logger import run_periodic_log_cleanup, DEFAULT_LOG_CLEANUP_INTERVAL_HOURS

        initialization_complete = Event()
        app.state.initialization_complete = initialization_complete

        # Set thread pool tokens from settings
        await set_threadpool_tokens(getattr(settings, 'thread_pool_tokens', DEFAULT_THREAD_POOL_TOKENS))

        # Start background log cleanup task
        cleanup_interval = getattr(settings, 'log_cleanup_interval_hours', DEFAULT_LOG_CLEANUP_INTERVAL_HOURS)
        cleanup_task: asyncio.Task[None] | None = None
        
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

            # Start automatic log cleanup task
            cleanup_task = asyncio.create_task(run_periodic_log_cleanup(cleanup_interval))
            logger.info(f"Started automatic log cleanup task (interval: {cleanup_interval} hours)")

            initialization_complete.set()
            yield

        finally:
            # Cancel log cleanup task
            if cleanup_task and not cleanup_task.done():
                cleanup_task.cancel()
                try:
                    await cleanup_task
                except asyncio.CancelledError:
                    pass

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

    # Add security scheme to OpenAPI schema for Swagger UI Authorize button
    # Override the openapi method to include security schemes
    original_openapi = application.openapi

    def custom_openapi():
        if application.openapi_schema:
            return application.openapi_schema
        openapi_schema = original_openapi()
        # Ensure components exist
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        if "securitySchemes" not in openapi_schema["components"]:
            openapi_schema["components"]["securitySchemes"] = {}
        
        # Add HTTPBearer security scheme
        openapi_schema["components"]["securitySchemes"]["HTTPBearer"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT access token. Token can be obtained from the /api/v1/auth/login endpoint."
        }
        
        application.openapi_schema = openapi_schema
        return application.openapi_schema

    application.openapi = custom_openapi

    return application

