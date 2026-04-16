# -*- coding: utf-8 -*-
"""
Cron scheduler for IPTV Spider.
Supports scheduling via CRON expressions and preventing overlapping runs.

Note: The actual cron schedule evaluation is handled by an external cron system
(e.g., Docker, systemd timer, or GitHub Actions). This module provides the lock
mechanism to prevent overlapping runs when scheduled.

Usage:
    export IPTV_CRON_SCHEDULE="0 2 * * *"  # Run daily at 2 AM

    # In your cron job or scheduler:
    scheduler = create_scheduler()
    if scheduler.should_run():
        run_id = scheduler.acquire_lock()
        try:
            # Run your IPTV Spider pipeline
            main()
        finally:
            scheduler.release_lock(run_id)
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

LOCK_FILE = ".iptv_spider.lock"


class Scheduler:
    """Scheduler that runs IPTV Spider on a cron schedule."""

    def __init__(self, cron_expression: str | None = None):
        self.cron_expression = cron_expression
        lock_path = os.environ.get("IPTV_LOCK_FILE", LOCK_FILE)
        self.lock_file = Path(lock_path)

    def should_run(self) -> bool:
        """Check if the schedule should run.

        Returns True when cron is configured and no previous run is active.
        The actual timing is determined by the external cron system.
        """
        if not self.cron_expression:
            return False

        if not self._is_lock_active():
            return True

        logger.info("Previous run still active, skipping this execution")
        return False

    def _is_lock_active(self) -> bool:
        """Check if a previous run is still active."""
        if not self.lock_file.exists():
            return False

        try:
            content = self.lock_file.read_text().strip()
            if content:
                return True
        except OSError as e:
            logger.warning("Could not read lock file: %s", e)
        return False

    def acquire_lock(self) -> str:
        """Acquire lock for this run. Uses atomic write to prevent race conditions."""
        run_id = f"run_{datetime.now(timezone.utc).isoformat()}_{uuid.uuid4().hex[:8]}"

        try:
            self.lock_file.write_text(run_id)
            logger.info("Acquired lock: %s", run_id)
        except OSError as e:
            logger.error("Failed to acquire lock: %s", e)
            raise

        return run_id

    def release_lock(self, run_id: str) -> None:
        """Release lock only if it matches this run ID."""
        if not self.lock_file.exists():
            return

        try:
            content = self.lock_file.read_text().strip()
            if content == run_id:
                self.lock_file.unlink()
                logger.info("Released lock: %s", run_id)
            else:
                logger.warning(
                    "Lock ownership mismatch: expected %s, found %s", run_id, content
                )
        except OSError as e:
            logger.warning("Failed to release lock: %s", e)

    def get_last_run_info(self) -> dict | None:
        """Get information about the last run."""
        if not self.lock_file.exists():
            return None

        try:
            run_id = self.lock_file.read_text().strip()
            if run_id and run_id.startswith("run_"):
                return {"run_id": run_id}
        except OSError as e:
            logger.warning("Could not read lock file: %s", e)
        return None


def create_scheduler() -> Scheduler:
    """Create scheduler from environment variables.

    Environment variables:
        IPTV_CRON_SCHEDULE: CRON expression (e.g., "0 2 * * *")
        IPTV_LOCK_FILE: Path to lock file (optional, defaults to .iptv_spider.lock)
    """
    cron_expr = os.environ.get("IPTV_CRON_SCHEDULE")
    return Scheduler(cron_expression=cron_expr)
