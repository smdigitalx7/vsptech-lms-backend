import sys
import psutil
import platform
from typing import Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.core.utils import cache, queue
from app.core.config import (
    settings,
    DB_HEALTH_CHECK_QUERY,
    MILLISECONDS_PER_SECOND,
    HEALTH_CPU_THRESHOLD_PERCENT,
    HEALTH_MEMORY_THRESHOLD_PERCENT,
    HEALTH_DISK_THRESHOLD_PERCENT,
    HEALTH_CPU_INTERVAL_SECONDS,
    BYTES_PER_GB,
)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live")
async def liveness_probe() -> dict[str, str]:
    """Liveness probe endpoint."""
    return {"status": "ok"}


@router.get("/ready")
async def readiness_probe() -> dict[str, object]:
    """Readiness probe endpoint with dependency checks."""
    db_ok = False
    redis_cache_ok = False
    redis_queue_ok = False

    # Database check
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text(DB_HEALTH_CHECK_QUERY))
        db_ok = True
    except Exception:
        db_ok = False

    # Redis cache check
    try:
        if cache.cache_manager.client is not None:
            pong = await cache.cache_manager.client.ping()  # type: ignore[misc]
            redis_cache_ok = bool(pong)
    except Exception:
        redis_cache_ok = False

    # Redis queue check
    try:
        if queue.pool is not None:
            info = await queue.pool.info()  # type: ignore[misc]
            redis_queue_ok = isinstance(info, dict)
    except Exception:
        redis_queue_ok = False

    overall = db_ok and (redis_cache_ok or cache.cache_manager.client is None) and (redis_queue_ok or queue.pool is None)

    return {
        "status": "ok" if overall else "degraded",
        "checks": {
            "database": db_ok,
            "redis_cache": redis_cache_ok if cache.cache_manager.client is not None else "not_configured",
            "redis_queue": redis_queue_ok if queue.pool is not None else "not_configured",
        },
    }


@router.get("/full")
async def comprehensive_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check for production monitoring.

    Checks:
    - Database connectivity and latency
    - Redis cache and queue connectivity
    - System resources (CPU, memory, disk)
    - Application metadata
    """
    import time as time_module

    health_data: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.environment.value if hasattr(settings, 'environment') else "unknown",
        "checks": {},
    }

    all_healthy = True

    # Database Check
    try:
        start_time = time_module.time()
        async with AsyncSessionLocal() as session:
            result = await session.execute(text(DB_HEALTH_CHECK_QUERY))
            result.fetchone()
        db_latency = (time_module.time() - start_time) * MILLISECONDS_PER_SECOND

        health_data["checks"]["database"] = {
            "status": "healthy",
            "latency_ms": round(db_latency, 2),
            "max_connections": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
        }
    except Exception as e:
        all_healthy = False
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # Redis Cache Check
    try:
        if cache.cache_manager.client is not None:
            start_time = time_module.time()
            pong = await cache.cache_manager.client.ping()  # type: ignore[misc]
            cache_latency = (time_module.time() - start_time) * MILLISECONDS_PER_SECOND

            health_data["checks"]["redis_cache"] = {
                "status": "healthy" if pong else "degraded",
                "latency_ms": round(cache_latency, 2),
                "configured": True,
            }
        else:
            health_data["checks"]["redis_cache"] = {
                "status": "not_configured",
                "configured": False,
            }
    except Exception as e:
        all_healthy = False
        health_data["checks"]["redis_cache"] = {
            "status": "unhealthy",
            "error": str(e),
            "configured": True,
        }

    # Redis Queue Check
    try:
        if queue.pool is not None:
            info = await queue.pool.info()  # type: ignore[misc]

            health_data["checks"]["redis_queue"] = {
                "status": "healthy",
                "client_count": info.get("connected_clients", 0),
                "version": info.get("redis_version", "unknown"),
                "configured": True,
            }
        else:
            health_data["checks"]["redis_queue"] = {
                "status": "not_configured",
                "configured": False,
            }
    except Exception as e:
        all_healthy = False
        health_data["checks"]["redis_queue"] = {
            "status": "unhealthy",
            "error": str(e),
            "configured": True,
        }

    # System Resources Check
    try:
        cpu_percent = psutil.cpu_percent(interval=HEALTH_CPU_INTERVAL_SECONDS)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        cpu_ok = cpu_percent < HEALTH_CPU_THRESHOLD_PERCENT
        memory_ok = memory.percent < HEALTH_MEMORY_THRESHOLD_PERCENT
        disk_ok = disk.percent < HEALTH_DISK_THRESHOLD_PERCENT

        resource_ok = cpu_ok and memory_ok and disk_ok
        if not resource_ok:
            all_healthy = False

        health_data["checks"]["system_resources"] = {
            "status": "healthy" if resource_ok else "warning",
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory.percent, 2),
            "memory_available_gb": round(memory.available / BYTES_PER_GB, 2),
            "disk_percent": round(disk.percent, 2),
            "disk_free_gb": round(disk.free / BYTES_PER_GB, 2),
            "threshold_warnings": {
                "cpu": not cpu_ok,
                "memory": not memory_ok,
                "disk": not disk_ok,
            }
        }
    except Exception as e:
        all_healthy = False
        health_data["checks"]["system_resources"] = {
            "status": "error",
            "error": str(e),
        }

    # Application Info
    try:
        health_data["application"] = {
            "name": settings.app_name if hasattr(settings, 'app_name') else "FastAPI App",
            "version": getattr(settings, 'app_version', '1.0.0'),
            "python_version": sys.version.split()[0],
            "platform": platform.system(),
            "debug_mode": settings.debug,
            "environment": settings.environment.value if hasattr(settings, 'environment') else "unknown",
        }
    except Exception as e:
        health_data["application"] = {
            "error": str(e),
        }

    health_data["status"] = "healthy" if all_healthy else "degraded"
    health_data["overall_healthy"] = all_healthy

    return health_data

