from arq.connections import RedisSettings
from app.core.config import settings, WORKER_MAX_JOBS, WORKER_JOB_TIMEOUT_SECONDS


class WorkerSettings:
    """ARQ worker configuration."""
    redis_settings = RedisSettings(
        host=settings.redis_queue_host,
        port=settings.redis_queue_port,
    )

    functions = [
        "src.app.core.worker.functions.example_task",
    ]

    max_jobs = WORKER_MAX_JOBS
    job_timeout = WORKER_JOB_TIMEOUT_SECONDS

