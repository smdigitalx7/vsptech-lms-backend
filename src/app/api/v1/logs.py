import json
import os
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.permissions import require_roles
from app.core.logger import LOG_FILE_PATHS, get_app_logger
from pydantic import BaseModel

router = APIRouter(prefix="/logs", tags=["Logs"])
logger = get_app_logger(__name__)


class LogEntry(BaseModel):
    """Single log entry model."""
    timestamp: str
    level: str
    logger: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line: Optional[int] = None
    request_id: Optional[str] = None
    category: Optional[str] = None
    exception: Optional[str] = None
    # Allow additional fields
    model_config = {"extra": "allow"}


class LogResponse(BaseModel):
    """Response model for log entries."""
    request_id: str
    entries: List[LogEntry]
    total_count: int
    log_files_searched: List[str]


def _get_log_directory() -> Optional[str]:
    """Get the log directory path."""
    # Try to get directory from any log file path
    for log_path in LOG_FILE_PATHS.values():
        if log_path:
            log_dir = os.path.dirname(log_path)
            if os.path.exists(log_dir):
                return log_dir
    return None


def _read_log_file(file_path: str, request_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Read and parse log file, optionally filtering by request_id.
    
    Parameters
    ----------
    file_path : str
        Path to the log file.
    request_id : Optional[str]
        Optional request_id to filter by.
    
    Returns
    -------
    List[Dict[str, Any]]
        List of parsed log entries matching the request_id (if provided).
    """
    entries = []
    
    if not os.path.exists(file_path):
        return entries
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    log_entry = json.loads(line)
                    
                    # Filter by request_id if provided
                    if request_id:
                        entry_request_id = log_entry.get("request_id")
                        if entry_request_id != request_id:
                            continue
                    
                    entries.append(log_entry)
                except json.JSONDecodeError:
                    # Skip invalid JSON lines
                    continue
    except Exception as e:
        logger.error(f"Error reading log file {file_path}: {e}", exc_info=True)
    
    return entries


@router.get("/request/{request_id}", response_model=LogResponse)
async def get_logs_by_request_id(
    request_id: str,
    log_category: Optional[str] = Query(
        None,
        description="Filter by log category (app, error, access, database, security). If not provided, searches all categories."
    ),
    current_user: dict[str, Any] = Depends(require_roles("SuperAdmin"))
) -> LogResponse:
    """
    Get all log entries for a specific request ID.
    
    This endpoint retrieves log entries from all log files (or a specific category)
    that match the given request_id. Useful for debugging and tracing requests
    across the application.
    
    Parameters
    ----------
    request_id : str
        The request ID to filter logs by.
    log_category : Optional[str]
        Optional log category to filter by. Options: app, error, access, database, security.
        If not provided, searches all log categories.
    current_user : dict
        Current authenticated user (must be SuperAdmin).
    
    Returns
    -------
    LogResponse
        Response containing all log entries matching the request_id.
    
    Raises
    ------
    HTTPException
        404 if no logs found for the request_id.
        500 if there's an error reading log files.
    """
    log_dir = _get_log_directory()
    
    if not log_dir:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Log directory not found or not accessible"
        )
    
    # Determine which log files to search
    log_files_to_search: Dict[str, str] = {}
    
    if log_category:
        # Search specific category
        if log_category not in LOG_FILE_PATHS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid log category: {log_category}. Valid options: {', '.join(LOG_FILE_PATHS.keys())}"
            )
        log_file_path = LOG_FILE_PATHS.get(log_category)
        if log_file_path:
            log_files_to_search[log_category] = log_file_path
    else:
        # Search all log files
        for category, log_file_path in LOG_FILE_PATHS.items():
            if log_file_path:
                log_files_to_search[category] = log_file_path
    
    all_entries: List[Dict[str, Any]] = []
    searched_files: List[str] = []
    
    # Read from each log file
    for category, log_file_path in log_files_to_search.items():
        if os.path.exists(log_file_path):
            entries = _read_log_file(log_file_path, request_id=request_id)
            all_entries.extend(entries)
            searched_files.append(f"{category}:{os.path.basename(log_file_path)}")
    
    # Sort entries by timestamp
    try:
        all_entries.sort(key=lambda x: x.get("timestamp", ""))
    except Exception:
        # If sorting fails, keep original order
        pass
    
    if not all_entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No log entries found for request_id: {request_id}"
        )
    
    # Convert to LogEntry models
    log_entries = [LogEntry(**entry) for entry in all_entries]
    
    return LogResponse(
        request_id=request_id,
        entries=log_entries,
        total_count=len(log_entries),
        log_files_searched=searched_files
    )


@router.get("/categories", response_model=List[str])
async def get_log_categories(
    current_user: dict[str, Any] = Depends(require_roles("SuperAdmin"))
) -> List[str]:
    """
    Get available log categories.
    
    Returns a list of available log categories that can be used
    to filter log searches.
    
    Parameters
    ----------
    current_user : dict
        Current authenticated user (must be SuperAdmin).
    
    Returns
    -------
    List[str]
        List of available log category names.
    """
    return list(LOG_FILE_PATHS.keys())

