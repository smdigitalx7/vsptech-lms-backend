"""Utility script to manually clean up old log files based on retention policy."""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src directory to path to import logger
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from app.core.logger import _get_log_config, _resolve_log_paths, DEFAULT_LOG_RETENTION_DAYS


def cleanup_old_logs(log_dir: str | None = None, retention_days: int | None = None) -> dict[str, int]:
    """
    Clean up log files older than retention_days.
    
    Args:
        log_dir: Directory to clean. If None, uses the resolved log directory.
        retention_days: Number of days to retain. If None, uses config value.
    
    Returns:
        Dictionary with 'deleted' count and 'kept' count of log files.
    """
    if log_dir is None:
        # Get the log directory from resolved paths
        log_paths = _resolve_log_paths()
        if not log_paths:
            print("No log directory found.")
            return {"deleted": 0, "kept": 0}
        
        # Get directory from first log path
        first_log_path = next((p for p in log_paths.values() if p), None)
        if not first_log_path:
            print("No log directory found.")
            return {"deleted": 0, "kept": 0}
        log_dir = os.path.dirname(first_log_path)
    
    if retention_days is None:
        log_config = _get_log_config()
        retention_days = log_config.get("retention_days", DEFAULT_LOG_RETENTION_DAYS)
    
    if not os.path.exists(log_dir):
        print(f"Log directory does not exist: {log_dir}")
        return {"deleted": 0, "kept": 0}
    
    cutoff_time = datetime.now() - timedelta(days=retention_days)
    log_path = Path(log_dir)
    
    deleted_count = 0
    kept_count = 0
    deleted_files = []
    
    # Find all log files (including rotated ones like .log.1, .log.2, etc.)
    for log_file in log_path.glob("*.log*"):
        try:
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_mtime < cutoff_time:
                log_file.unlink()
                deleted_count += 1
                deleted_files.append(log_file.name)
                print(f"Deleted old log file: {log_file.name} (last modified: {file_mtime.strftime('%Y-%m-%d %H:%M:%S')})")
            else:
                kept_count += 1
        except (OSError, ValueError) as e:
            print(f"Error processing {log_file.name}: {e}")
            continue
    
    print(f"\nCleanup complete:")
    print(f"  Retention policy: {retention_days} days")
    print(f"  Cutoff date: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Files deleted: {deleted_count}")
    print(f"  Files kept: {kept_count}")
    
    if deleted_files:
        print(f"\nDeleted files: {', '.join(deleted_files)}")
    
    return {"deleted": deleted_count, "kept": kept_count}


if __name__ == "__main__":
    """Run cleanup when script is executed directly."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up old log files based on retention policy")
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="Log directory to clean (default: auto-detect from config)"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=None,
        help=f"Number of days to retain logs (default: from config, fallback: {DEFAULT_LOG_RETENTION_DAYS})"
    )
    
    args = parser.parse_args()
    
    cleanup_old_logs(log_dir=args.log_dir, retention_days=args.retention_days)

