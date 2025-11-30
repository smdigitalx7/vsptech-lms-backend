import logging
import os
import sys
import queue
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
from typing import Any, Optional
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ============================================================================
# Constants
# ============================================================================
# Default log rotation settings
DEFAULT_LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_LOG_BACKUP_COUNT = 5
DEFAULT_LOG_RETENTION_DAYS = 30
DEFAULT_LOG_CLEANUP_INTERVAL_HOURS = 24  # Run cleanup once per day

# ============================================================================
# Helper Functions
# ============================================================================
# Resolve a writable log directory
def _resolve_log_paths() -> dict[str, Optional[str]]:
    """
    Resolve log directory paths.
    Tries /app/logs for Docker, then local logs directory (src/app/logs).
    Does not fall back to /tmp to ensure logs are stored in proper locations.
    """
    # Get the app directory (one level up from core/logger.py)
    # This points to src/app/logs which is the existing logs directory
    app_dir = os.path.dirname(os.path.dirname(__file__))
    local_logs_dir = os.path.join(app_dir, "logs")
    
    # Try Docker logs directory first, then local logs directory
    log_dirs = [
        "/app/logs",  # Docker volume mount (writable)
        local_logs_dir,  # Local development - src/app/logs
    ]
    
    for base_dir in log_dirs:
        try:
            # Create directory if it doesn't exist
            os.makedirs(base_dir, exist_ok=True)
            # Test write permissions
            test_file = os.path.join(base_dir, ".write_test")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
                # If we get here, directory is writable
                return {
                    "app": os.path.join(base_dir, "app.log"),
                    "error": os.path.join(base_dir, "error.log"),
                    "access": os.path.join(base_dir, "access.log"),
                    "database": os.path.join(base_dir, "database.log"),
                    "security": os.path.join(base_dir, "security.log")
                }
            except (PermissionError, OSError):
                continue
        except (PermissionError, OSError):
            continue
    
    # If no writable directory found, return None for all paths
    # This will cause logging to only use console output
    return {key: None for key in ["app", "error", "access", "database", "security"]}


# Get logging level from config or environment variable
def _get_logging_level() -> int:
    """Get logging level from settings or environment variable."""
    try:
        from .config import settings
        level_str = settings.log_level.upper()
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return level_map.get(level_str, logging.INFO)
    except (ImportError, AttributeError):
        # Fallback to DEBUG environment variable if config not available
        return logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO


# ============================================================================
# Module-level Variables (initialized after helper functions)
# ============================================================================
LOG_FILE_PATHS: dict[str, Optional[str]] = _resolve_log_paths()
LOGGING_LEVEL = _get_logging_level()

# Global queue and listener for async logging
_log_queue: Optional[queue.Queue[logging.LogRecord]] = None
_log_listener: Optional[QueueListener] = None


# ============================================================================
# Configuration Functions
# ============================================================================
def _get_log_config() -> dict[str, Any]:
    """Get log configuration from settings, with fallback to defaults."""
    try:
        from .config import settings
        return {
            "max_bytes": getattr(settings, "log_file_max_size", DEFAULT_LOG_MAX_SIZE),
            "backup_count": getattr(settings, "log_file_backup_count", DEFAULT_LOG_BACKUP_COUNT),
            "retention_days": getattr(settings, "log_retention_days", DEFAULT_LOG_RETENTION_DAYS),
            "log_format": getattr(settings, "log_format", "json"),
        }
    except (ImportError, AttributeError):
        return {
            "max_bytes": DEFAULT_LOG_MAX_SIZE,
            "backup_count": DEFAULT_LOG_BACKUP_COUNT,
            "retention_days": DEFAULT_LOG_RETENTION_DAYS,
            "log_format": "json",
        }

def _cleanup_old_logs(log_dir: str, retention_days: int) -> dict[str, int]:
    """
    Clean up log files older than retention_days.
    
    This function removes log files (including rotated backups like .log.1, .log.2, etc.)
    that are older than the specified retention period.
    
    Returns:
        Dictionary with 'deleted' and 'kept' counts
    """
    if not log_dir or not os.path.exists(log_dir):
        return {"deleted": 0, "kept": 0}
    
    try:
        cutoff_time = datetime.now() - timedelta(days=retention_days)
        log_path = Path(log_dir)
        deleted_count = 0
        kept_count = 0
        
        # Find all log files including rotated backups (*.log, *.log.1, *.log.2, etc.)
        for log_file in log_path.glob("*.log*"):
            try:
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_mtime < cutoff_time:
                    log_file.unlink()
                    deleted_count += 1
                else:
                    kept_count += 1
            except (OSError, ValueError):
                continue
        
        return {"deleted": deleted_count, "kept": kept_count}
    except Exception:
        return {"deleted": 0, "kept": 0}


async def run_periodic_log_cleanup(interval_hours: int = DEFAULT_LOG_CLEANUP_INTERVAL_HOURS) -> None:
    """
    Background task to periodically clean up old log files.
    
    Args:
        interval_hours: Hours between cleanup runs (default: 24 hours)
    """
    import asyncio
    
    logger = get_app_logger("log_cleanup")
    
    while True:
        try:
            await asyncio.sleep(interval_hours * 3600)  # Convert hours to seconds
            
            log_config = _get_log_config()
            retention_days = log_config.get("retention_days", DEFAULT_LOG_RETENTION_DAYS)
            log_paths = LOG_FILE_PATHS
            
            total_deleted = 0
            total_kept = 0
            
            for log_path in log_paths.values():
                if log_path:
                    log_dir = os.path.dirname(log_path)
                    result = _cleanup_old_logs(log_dir, retention_days)
                    total_deleted += result["deleted"]
                    total_kept += result["kept"]
            
            if total_deleted > 0:
                logger.info(
                    f"Automatic log cleanup completed: {total_deleted} file(s) deleted, "
                    f"{total_kept} file(s) kept (retention: {retention_days} days)"
                )
        except asyncio.CancelledError:
            logger.info("Log cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error during automatic log cleanup: {e}", exc_info=True)
            # Continue running even if cleanup fails
            await asyncio.sleep(3600)  # Wait 1 hour before retrying on error

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    RESERVED_ATTRS = {
        'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
        'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
        'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
        'processName', 'process', 'message', 'asctime', 'getMessage'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        request_id = getattr(record, "request_id", None)
        if request_id:
            log_entry["request_id"] = request_id
        
        if record.exc_info:
            try:
                log_entry["exception"] = self.formatException(record.exc_info)
            except Exception:
                log_entry["exception"] = str(record.exc_info)
        
        for key, value in record.__dict__.items():
            if key not in self.RESERVED_ATTRS and not key.startswith('_'):
                try:
                    if key not in log_entry:
                        json.dumps(value, default=str)
                        log_entry[key] = value
                except (TypeError, ValueError):
                    log_entry[key] = str(value)
        
        return json.dumps(log_entry, default=str)


class TextFormatter(logging.Formatter):
    """Standard text formatter for human-readable logging."""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


class CategoryFilter(logging.Filter):
    """Filter logs by category to route them to the correct file."""
    
    def __init__(self, category: str):
        super().__init__()
        self.category = category
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Return True if the log record matches this category."""
        record_category = getattr(record, 'category', 'app')
        return record_category == self.category


def _get_formatter(log_format: str = "json") -> logging.Formatter:
    """Get formatter based on log format setting."""
    if log_format.lower() == "text":
        return TextFormatter()
    return JSONFormatter()

def _setup_async_logging() -> None:
    """Setup global async logging infrastructure using QueueHandler and QueueListener."""
    global _log_queue, _log_listener
    
    if _log_queue is not None:
        return
    
    _log_queue = queue.Queue[logging.LogRecord](-1)
    handlers: list[logging.Handler] = []
    
    log_config = _get_log_config()
    formatter = _get_formatter(log_config.get("log_format", "json"))
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOGGING_LEVEL)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # Create category-specific file handlers with filters
    for category, log_path in LOG_FILE_PATHS.items():
        if log_path:
            try:
                log_dir = os.path.dirname(log_path)
                
                file_handler = RotatingFileHandler(
                    log_path,
                    maxBytes=log_config["max_bytes"],
                    backupCount=log_config["backup_count"],
                    encoding="utf-8",
                )
                file_handler.setLevel(LOGGING_LEVEL)
                file_handler.setFormatter(formatter)
                # Add category filter so only logs of this category go to this file
                file_handler.addFilter(CategoryFilter(category))
                handlers.append(file_handler)
                
                _cleanup_old_logs(log_dir, log_config["retention_days"])
            except Exception:
                pass
    
    _log_listener = QueueListener(_log_queue, *handlers, respect_handler_level=True)
    _log_listener.start()

def stop_async_logging() -> None:
    """Stop the async logging listener (call on application shutdown)."""
    global _log_listener
    if _log_listener is not None:
        _log_listener.stop()
        _log_listener = None

class StructuredLogger:
    """Structured logger with category-based file logging."""
    
    def __init__(self, name: str, category: str = "app"):
        _setup_async_logging()
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOGGING_LEVEL)
        self.category = category
        
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        log_config = _get_log_config()
        formatter = _get_formatter(log_config.get("log_format", "json"))
        
        if _log_queue is not None:
            queue_handler = QueueHandler(_log_queue)
            queue_handler.setLevel(LOGGING_LEVEL)
            self.logger.addHandler(queue_handler)
        else:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(LOGGING_LEVEL)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def _log_with_context(self, level: int, message: str, **kwargs: Any) -> None:
        """Log with additional context."""
        exc_info = kwargs.pop('exc_info', None)
        # Add category to extra so filters can route to correct file
        kwargs['category'] = self.category
        if kwargs:
            self.logger.log(level, message, extra=kwargs, exc_info=exc_info)
        else:
            self.logger.log(level, message, extra={'category': self.category}, exc_info=exc_info)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exc_info: Optional[bool] = None, **kwargs: Any) -> None:
        """Log error message with context."""
        if exc_info is not None:
            kwargs['exc_info'] = exc_info
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message with context."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)

def get_logger(name: str, category: str = "app") -> StructuredLogger:
    """Get a structured logger instance with specified category."""
    return StructuredLogger(name, category)

def get_app_logger(name: str) -> StructuredLogger:
    """Get an application logger (general app logs)."""
    return StructuredLogger(name, "app")

def get_error_logger(name: str) -> StructuredLogger:
    """Get an error logger (errors, exceptions, critical issues)."""
    return StructuredLogger(name, "error")

def get_access_logger(name: str) -> StructuredLogger:
    """Get an access logger (API requests, responses, user actions)."""
    return StructuredLogger(name, "access")

def get_database_logger(name: str) -> StructuredLogger:
    """Get a database logger (DB queries, connections, transactions)."""
    return StructuredLogger(name, "database")

def get_security_logger(name: str) -> StructuredLogger:
    """Get a security logger (authentication, authorization, security events)."""
    return StructuredLogger(name, "security")

# Configure root logger with async logging
_setup_async_logging()
root_logger = logging.getLogger()
root_logger.setLevel(LOGGING_LEVEL)

for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

if _log_queue is not None:
    queue_handler = QueueHandler(_log_queue)
    queue_handler.setLevel(LOGGING_LEVEL)
    root_logger.addHandler(queue_handler)

