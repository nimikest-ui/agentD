"""Configure JSON logging for agentD."""

import json
import logging
import sys
from pathlib import Path


def setup_logging(log_file: str | Path = None):
    """Set up JSON logging for agentD components.

    Args:
        log_file: Path to write logs. If None, logs only to stdout.
    """
    log_file = log_file or Path.home() / ".agentd" / "logs" / "agentd.log"

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

    print(f"Logging configured. Logs written to: {log_file}", file=sys.stderr)
