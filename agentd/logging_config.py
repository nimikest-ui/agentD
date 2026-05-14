"""Configure JSON logging for agentD."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path


# Global reference to current log file for exit handler
_current_log_file = None


def setup_logging(log_file: str | Path = None):
    """Set up JSON logging for agentD components.

    Args:
        log_file: Path to write logs. If None, creates timestamped file in sessions dir.
    """
    global _current_log_file

    if log_file is None:
        # Create sessions directory with timestamped log file
        sessions_dir = Path.home() / ".agentd" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = sessions_dir / f"session_{timestamp}.log"

    _current_log_file = log_file

    # Ensure log directory exists
    if isinstance(log_file, str):
        log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                "timestamp": self.formatTime(record),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if record.exc_info:
                log_obj["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_obj)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # File handler (JSON)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)

    # Console handler (JSON to stdout for debugging)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    for logger_name in ["agentd.kimi", "agentd.graph", "agentd.core"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

    # Register exit handler to show log file path on quit
    import atexit
    def print_log_on_exit():
        if _current_log_file and _current_log_file.exists():
            # Get file size
            size = _current_log_file.stat().st_size
            print(f"\n📋 Session logs saved to: {_current_log_file} ({size} bytes)", file=sys.stderr)

    atexit.register(print_log_on_exit)

    # Also print at startup
    print(f"📝 Logging to: {log_file}", file=sys.stderr)
