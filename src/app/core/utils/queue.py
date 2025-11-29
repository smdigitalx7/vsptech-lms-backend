from arq import ArqRedis
from typing import Any

pool: ArqRedis | None = None


async def enqueue_job(function_name: str, *args: Any, **kwargs: Any) -> str | None:
    """Enqueue a background job.

    Parameters
    ----------
    function_name : str
        The name of the function to execute.
    *args : Any
        Positional arguments for the function.
    **kwargs : Any
        Keyword arguments for the function.

    Returns
    -------
    str | None
        Job ID if successful, None otherwise.
    """
    if pool is None:
        return None

    try:
        job = await pool.enqueue_job(function_name, *args, **kwargs)
        return job.job_id if job else None
    except Exception:
        return None


async def get_job_status(job_id: str) -> dict[str, Any] | None:
    """Get the status of a background job.

    Parameters
    ----------
    job_id : str
        The job ID to check.

    Returns
    -------
    dict[str, Any] | None
        Job status information if found, None otherwise.
    """
    if pool is None:
        return None

    try:
        return await pool.get_job_status(job_id)  # type: ignore[return-value, misc]
    except Exception:
        return None

