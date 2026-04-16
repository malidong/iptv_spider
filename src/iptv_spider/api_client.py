# -*- coding: utf-8 -*-
"""
HTTP client for API sync with retry and backoff support.
"""

import time
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class SyncResult:
    """Result of an API sync operation."""

    success: bool
    status_code: int | None
    error_message: str | None
    retry_count: int


class APIClient:
    """HTTP client with retry and backoff."""

    def __init__(
        self,
        endpoint: str,
        token: str | None = None,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        self.endpoint = endpoint
        self.token = token
        self.max_retries = max_retries
        self.timeout = timeout
        self.headers: dict[str, str] = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def post(self, payload: dict[str, Any]) -> SyncResult:
        """POST payload to endpoint with retry."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout,
                )
                if response.status_code < 400:
                    return SyncResult(
                        success=True,
                        status_code=response.status_code,
                        error_message=None,
                        retry_count=attempt,
                    )
                last_error = f"HTTP {response.status_code}: {response.text}"
            except requests.RequestException as e:
                last_error = str(e)

            if attempt < self.max_retries - 1:
                wait_time = 2**attempt
                time.sleep(wait_time)

        return SyncResult(
            success=False,
            status_code=None,
            error_message=last_error,
            retry_count=self.max_retries - 1,
        )
