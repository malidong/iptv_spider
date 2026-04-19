# -*- coding: utf-8 -*-
"""
Unit tests for health check module.
"""

import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock

from iptv_spider.health import (
    HealthStatus,
    check_system,
    check_network,
    check_disk,
    run_health_check,
)


class TestHealthStatus(TestCase):
    def test_health_status_creation(self):
        status = HealthStatus(status="healthy", component="system", message=None)
        self.assertEqual(status.status, "healthy")
        self.assertEqual(status.component, "system")
        self.assertIsNone(status.message)


class TestCheckSystem(TestCase):
    def test_check_system_healthy(self):
        status = check_system()
        self.assertEqual(status.component, "system")


class TestCheckNetwork(TestCase):
    def test_check_network_disabled_returns_none(self):
        status = check_network(enabled=False)
        self.assertIsNone(status)

    @patch("requests.get")
    def test_check_network_healthy(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        status = check_network(enabled=True)
        self.assertEqual(status.status, "healthy")

    @patch("requests.get")
    def test_check_network_unhealthy(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        status = check_network(enabled=True)
        self.assertEqual(status.status, "unhealthy")
        self.assertIn("Network error", status.message)


class TestCheckDisk(TestCase):
    def test_check_disk_healthy(self):
        with patch("iptv_spider.utils.get_config_dir") as mock_dir:
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = True
            mock_path.parent.exists.return_value = True
            mock_dir.return_value = mock_path

            status = check_disk()
            self.assertEqual(status.status, "healthy")


class TestRunHealthCheck(TestCase):
    @patch("iptv_spider.health.check_system")
    @patch("iptv_spider.health.check_network")
    @patch("iptv_spider.health.check_disk")
    def test_run_health_check_all_pass(self, mock_disk, mock_network, mock_system):
        mock_system.return_value = HealthStatus("healthy", "system", None)
        mock_network.return_value = HealthStatus("healthy", "network", None)
        mock_disk.return_value = HealthStatus("healthy", "disk", None)

        result = run_health_check(verbose=False)
        self.assertTrue(result)

    @patch("iptv_spider.health.check_system")
    @patch("iptv_spider.health.check_network")
    @patch("iptv_spider.health.check_disk")
    def test_run_health_check_with_network_disabled(self, mock_disk, mock_network, mock_system):
        mock_system.return_value = HealthStatus("healthy", "system", None)
        mock_network.return_value = None
        mock_disk.return_value = HealthStatus("healthy", "disk", None)

        os.environ["IPTV_HEALTH_CHECK_NETWORK"] = "0"
        try:
            result = run_health_check(verbose=False)
            self.assertTrue(result)
        finally:
            del os.environ["IPTV_HEALTH_CHECK_NETWORK"]
