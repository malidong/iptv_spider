# -*- coding: utf-8 -*-
"""
Sync exporter for pushing results to external API.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from iptv_spider.api_client import APIClient


@dataclass
class SyncError:
    """Represents a sync error."""

    field: str
    message: str


class SyncExporter:
    """Exports channels to external API with local backup."""

    def __init__(
        self,
        endpoint: str,
        token: str | None = None,
        max_retries: int = 3,
        timeout: int = 30,
        backup_dir: str = "backups",
    ):
        self.client = APIClient(endpoint, token, max_retries, timeout)
        self.backup_dir = backup_dir
        self._ensure_backup_dir()

    def _ensure_backup_dir(self) -> None:
        """Create backup directory if needed."""
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)

    def sync_and_backup(
        self, channels: dict[str, Any], filename: str
    ) -> list[SyncError]:
        """Sync to API, fallback to local backup on failure."""
        errors: list[SyncError] = []

        payload = {
            "channels": channels,
            "timestamp": str(Path(filename).stem),
        }

        result = self.client.post(payload)

        if result.success:
            return errors

        errors.append(
            SyncError(
                field="api_sync",
                message=f"Sync failed: {result.error_message}",
            )
        )

        backup_path = self._create_backup(channels, filename)
        if backup_path:
            errors.append(
                SyncError(
                    field="backup",
                    message=f"Created backup at: {backup_path}",
                )
            )

        return errors

    def _create_backup(self, channels: dict[str, Any], filename: str) -> str | None:
        """Create local backup file."""
        try:
            backup_filename = f"{filename}.backup.json"
            backup_path = Path(self.backup_dir) / backup_filename
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(channels, f, indent=2, ensure_ascii=False)
            return str(backup_path)
        except OSError:
            return None


def create_sync_exporter(
    endpoint: str,
    token: str | None = None,
    max_retries: int = 3,
    timeout: int = 30,
    backup_dir: str = "backups",
) -> SyncExporter:
    """Factory function to create SyncExporter."""
    return SyncExporter(
        endpoint=endpoint,
        token=token,
        max_retries=max_retries,
        timeout=timeout,
        backup_dir=backup_dir,
    )
