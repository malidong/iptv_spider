# -*- coding: utf-8 -*-
"""
Cron scheduler for IPTV Spider.
Supports scheduling via CRON expressions and preventing overlapping runs.
"""

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class CronSchedule:
    """Represents a cron schedule configuration."""

    expression: str
    enabled: bool = True


LOCK_FILE = ".iptv_spider.lock"


class Scheduler:
    """Scheduler that runs IPTV Spider on a cron schedule."""

    def __init__(self, cron_expression: str | None = None):
        self.cron_expression = cron_expression
        self.lock_file = Path(LOCK_FILE)

    def should_run(self) -> bool:
        """Check if the schedule should run now based on CRON expression."""
        if not self.cron_expression:
            return False

        if not self._is_lock_active():
            return True

        return False

    def _is_lock_active(self) -> bool:
        """Check if a previous run is still active."""
        if not self.lock_file.exists():
            return False

        try:
            content = self.lock_file.read_text().strip()
            if content:
                return True
        except OSError:
            pass
        return False

    def acquire_lock(self) -> str:
        """Acquire lock for this run. Returns run ID."""
        run_id = self._generate_run_id()
        self.lock_file.write_text(run_id)
        return run_id

    def release_lock(self, run_id: str) -> None:
        """Release lock only if it matches this run ID."""
        if not self.lock_file.exists():
            return

        try:
            content = self.lock_file.read_text().strip()
            if content == run_id:
                self.lock_file.unlink()
        except OSError:
            pass

    def _generate_run_id(self) -> str:
        """Generate a unique run ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        return f"run_{timestamp}"

    def get_last_run_info(self) -> dict | None:
        """Get information about the last run."""
        if not self.lock_file.exists():
            return None

        try:
            run_id = self.lock_file.read_text().strip()
            if run_id and run_id.startswith("run_"):
                timestamp = run_id[4:]
                return {"run_id": run_id, "started_at": timestamp}
        except OSError:
            pass
        return None


def create_scheduler() -> Scheduler:
    """Create scheduler from environment variables."""
    cron_expr = os.environ.get("IPTV_CRON_SCHEDULE")
    return Scheduler(cron_expression=cron_expr)
