from typing import Any
from app.core.logger import get_app_logger

logger = get_app_logger(__name__)


async def example_task(ctx: dict[str, Any], message: str) -> str:
    """Example background task.

    Parameters
    ----------
    ctx : dict[str, Any]
        ARQ context dictionary.
    message : str
        Message to process.

    Returns
    -------
    str
        Processed result.
    """
    logger.info(f"Processing background task with message: {message}")
    # Simulate some work
    return f"Processed: {message}"

