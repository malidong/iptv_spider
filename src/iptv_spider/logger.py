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

import logging
import os

# Log directory and file name
LOG_DIR: str = "./logs"
LOG_FILE: str = "application.log"

# Ensure the log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Create a global Logger
logger: logging.Logger = logging.getLogger("iptv_spider")
logger.setLevel(logging.DEBUG)  # Set global log level

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

# Add handlers to the Logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)
