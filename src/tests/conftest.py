"""
Pytest configuration and fixtures for testing.

This module provides core test fixtures for:
- Database session management
- FastAPI test application
- Redis mock clients
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

try:
    from app.core.config import EnvironmentOption, Settings
    from app.core.setup import create_application
    from app.core.database import get_db_session
    from app.api import router
    from app.core.logger import get_logger
    from app.models.base import Base
    from app.models.user import User
except Exception as e:
    print(f"DEBUG: Failed to import in conftest: {e}")
    import traceback
    traceback.print_exc()
    raise e

logger = get_logger(__name__)


def _apply_test_settings(test_config: Settings) -> None:
    """Replace global settings references so application code uses test configuration."""
    import app.core.config as core_config

    core_config.settings = test_config


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine(test_settings: Settings) -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine."""
    from urllib.parse import quote_plus
    import os

    test_db_name = os.getenv("TEST_DATABASE_NAME", "test_database")
    encoded_password = quote_plus(test_settings.postgres_password)

    test_db_url = (
        f"postgresql+asyncpg://{test_settings.postgres_user}:{encoded_password}"
        f"@{test_settings.postgres_server}:{test_settings.postgres_port}/{test_db_name}"
    )

    test_engine = create_async_engine(
        test_db_url,
        echo=False,
        future=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
    )

    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(
    db_engine: AsyncEngine,
    test_settings: Settings,
) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    connection = await db_engine.connect()
    transaction = await connection.begin()

    TestAsyncSession = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    session = TestAsyncSession()
    await session.begin_nested()

    def _restart_savepoint(sess, trans):
        parent = getattr(trans, "_parent", None)
        if trans.nested and parent and not parent.nested:
            sess.begin_nested()

    event.listen(session.sync_session, "after_transaction_end", _restart_savepoint)

    try:
        yield session
    finally:
        await session.rollback()
        await session.close()
        await transaction.rollback()
        await connection.close()
        event.remove(session.sync_session, "after_transaction_end", _restart_savepoint)


@pytest.fixture(scope="function")
def override_get_db(db_session: AsyncSession):
    """Override the get_db dependency to use the test database session."""
    async def _get_db_test() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield db_session
        finally:
            pass

    return _get_db_test


@pytest.fixture(scope="function")
def test_settings() -> Settings:
    """Create test-specific settings."""
    settings = Settings(
        app_name="FastAPI Template Test",
        app_description="FastAPI Template Test Application",
        app_version="0.1.0-test",
        debug=True,

        # Security
        secret_key=SecretStr("test-secret-key-32-characters-long!!"),
        algorithm="HS256",
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,

        # Database
        postgres_user="test",
        postgres_password="test",
        postgres_server="localhost",
        postgres_port=5432,
        postgres_db="test_db",

        # Redis
        redis_cache_host="localhost",
        redis_cache_port=6379,
        redis_queue_host="localhost",
        redis_queue_port=6379,
        redis_rate_limit_host="localhost",
        redis_rate_limit_port=6379,

        # Cache
        client_cache_max_age=60,

        # Rate limiting
        default_rate_limit_limit=10000,
        default_rate_limit_period=60,

        # Database pool
        db_pool_size=5,
        db_max_overflow=10,
        db_pool_timeout=30,
        db_pool_recycle=3600,

        # API configuration
        default_page_size=20,
        max_page_size=100,
        default_page=1,

        # Logging
        log_level="DEBUG",
        log_format="text",
        log_file_max_size=10485760,
        log_file_backup_count=5,
        log_retention_days=30,

        # CORS
        cors_origins="http://localhost:3000,http://localhost:8080",
        cors_allow_credentials=True,
        cors_max_age=3600,
        cors_allow_headers="Authorization,Content-Type",
        cors_expose_headers="X-Total-Count,X-Page-Count",
        cors_allow_methods="GET,POST,PUT,DELETE,OPTIONS",

        # Environment
        environment=EnvironmentOption.LOCAL,

        # Auth paths
        skip_auth_paths={"/health", "/docs", "/redoc", "/openapi.json"},
        refresh_paths={"/api/v1/auth/refresh"},

        # Thread pool
        thread_pool_tokens=100,
    )

    _apply_test_settings(settings)
    return settings


@pytest_asyncio.fixture(scope="function")
async def app(
    override_get_db,
    test_settings: Settings,
) -> AsyncGenerator[FastAPI, None]:
    """Create a test FastAPI application instance."""
    _ = test_settings
    import fakeredis.aioredis
    import anyio
    from app.core.utils import cache, queue
    from fastapi.middleware.cors import CORSMiddleware

    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        """Simplified lifespan for testing."""
        from asyncio import Event

        initialization_complete = Event()
        app.state.initialization_complete = initialization_complete

        try:
            try:
                limiter = anyio.CapacityLimiter(100)
                setattr(anyio.to_thread, "current_default_thread_limiter", limiter)
            except AttributeError:
                try:
                    limiter = getattr(anyio.to_thread, "current_default_thread_limiter", None)
                    if limiter is not None:
                        limiter.total_tokens = 100
                except Exception as e:
                    logger.warning(f"Failed to set thread pool limiter: {e}")

            fake_redis = await fakeredis.aioredis.FakeRedis(decode_responses=True)

            cache.cache_manager.client = fake_redis
            cache.cache_manager._is_connected = True

            queue.pool = fake_redis

            initialization_complete.set()
            yield

        finally:
            if cache.cache_manager.client:
                await cache.cache_manager.disconnect()
            if queue.pool:
                await queue.pool.aclose()

    application = create_application(router=router, lifespan=test_lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=3600,
    )

    application.dependency_overrides[get_db_session] = override_get_db

    yield application

    application.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for making HTTP requests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
def sync_client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Create a synchronous test client for making HTTP requests."""
    with TestClient(app=app, base_url="http://test") as tc:
        yield tc

