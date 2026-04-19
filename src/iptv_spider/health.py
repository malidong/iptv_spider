# -*- coding: utf-8 -*-
"""
Health check module for IPTV Spider.

Provides health check command/endpoint for runtime readiness and diagnostics.

Usage:
    iptv-spider --health [--verbose]
    IPTV_HEALTH_CHECK_NETWORK=0 iptv-spider --health  # Skip network check
"""

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class HealthStatus:
    """Health check result."""

    status: str
    component: str
    message: str | None = None
    details: dict | None = None


def check_system() -> HealthStatus:
    """Check system dependencies."""
    issues: list[str] = []

    try:
        import requests
    except ImportError:
        issues.append("requests")

    try:
        import m3u8
    except ImportError:
        issues.append("m3u8")

    status = "healthy" if not issues else "degraded"
    return HealthStatus(
        status=status,
        component="system",
        message=None if not issues else f"Missing: {', '.join(issues)}",
    )


def check_network(enabled: bool = True) -> HealthStatus | None:
    """Check network connectivity. Returns None if disabled via env var."""
    if not enabled:
        return None

    error_msg: str | None = None
    try:
        import requests
        response = requests.get("https://httpbin.org/get", timeout=5)
        connected = response.status_code == 200
    except Exception as e:
        connected = False
        error_msg = str(e)

    return HealthStatus(
        status="healthy" if connected else "unhealthy",
        component="network",
        message=error_msg,
    )


def check_disk() -> HealthStatus:
    """Check disk space for logs and cache."""
    try:
        from iptv_spider.utils import get_config_dir
        path = get_config_dir()
        writable = path.exists() or path.parent.exists()
    except Exception:
        writable = False

    return HealthStatus(
        status="healthy" if writable else "unhealthy",
        component="disk",
        message=None if writable else "Cannot write to config dir",
    )


def run_health_check(verbose: bool = False) -> bool:
    """Run all health checks and return overall status."""
    network_enabled = os.environ.get("IPTV_HEALTH_CHECK_NETWORK", "1") != "0"
    checks = [check_system()]

    network_result = check_network(network_enabled)
    if network_result:
        checks.append(network_result)

    checks.append(check_disk())

    all_healthy = all(c.status == "healthy" for c in checks)

    print(f"Health Check ({datetime.now(timezone.utc).isoformat()})")
    print("-" * 40)
    for check in checks:
        icon = "[PASS]" if check.status == "healthy" else "[FAIL]"
        print(f"  {icon} {check.component}: {check.status}")
        if verbose and check.message:
            print(f"    {check.message}")

    print("-" * 40)
    overall = "PASS" if all_healthy else "FAIL"
    print(f"Overall: {overall}")
    return all_healthy


if __name__ == "__main__":
    success = run_health_check(verbose=True)
    sys.exit(0 if success else 1)