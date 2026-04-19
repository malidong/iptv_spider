# -*- coding: utf-8 -*-
# pylint: disable=line-too-long

"""
Module for setting up logging configuration for IPTV Spider application.

This module creates and configures a logger to log messages both to a file and the console.
It ensures that the log directory exists, sets up log levels for different handlers, and defines
the log format.

Log messages are written to:
1. A file located in the "./logs" directory with the name "application.log"
2. The console, displaying debug-level logs and higher.

The logging setup supports two handlers:
- FileHandler: Writes logs at INFO level and higher to a file.
- StreamHandler: Displays logs at DEBUG level and higher on the console.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from iptv_spider.utils import get_config_dir

# Log directory and file name
try:
    LOG_DIR: Path = get_config_dir() / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError):
    # Fall back to a local path when HOME/config dir is not writable
    LOG_DIR = Path.cwd() / ".iptv-spider" / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE: str = f"{datetime.today().strftime('%Y-%m-%d')}.log"

# Create a global Logger
logger: logging.Logger = logging.getLogger("iptv_spider")
logger.setLevel(logging.INFO)  # Set global log level

# Create log format
formatter: logging.Formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create file handler
file_handler: logging.FileHandler = logging.FileHandler(os.path.join(LOG_DIR, LOG_FILE), encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Create console handler
console_handler: logging.StreamHandler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Add handlers to the Logger only once
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def create_run_id() -> str:
    """Create a unique run ID for tracking."""
    return uuid.uuid4().hex[:8]


def log_structured(
    level: int,
    message: str,
    run_id: str = "",
    stage: str = "",
    source: str = "",
    latency_ms: float | None = None,
    **kwargs: Any,
) -> None:
    """Log with structured fields for machine parsing."""
    extra = {
        "run_id": run_id,
        "stage": stage,
        "source": source,
        "latency_ms": latency_ms,
    }
    extra = {k: v for k, v in extra.items() if v}
    logger.log(level, message, extra=extra)


def log_event(
    event: str,
    run_id: str = "",
    stage: str = "",
    status: str = "info",
    **kwargs: Any,
) -> None:
    """Log structured event for observability."""
    data = {
        "event": event,
        "run_id": run_id,
        "stage": stage,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    data.update({k: v for k, v in kwargs.items() if v is not None})
    logger.info(json.dumps(data))
