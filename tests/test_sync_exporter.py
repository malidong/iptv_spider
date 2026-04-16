# -*- coding: utf-8 -*-
"""Tests for API sync exporter."""

import json
import unittest
from pathlib import Path
import tempfile

from iptv_spider.sync_exporter import SyncError, create_sync_exporter
from iptv_spider.api_client import APIClient


class TestAPIClient(unittest.TestCase):
    """Test API client."""

    def test_client_initialization(self):
        """Test client is initialized with correct values."""
        client = APIClient(
            endpoint="http://example.com/api",
            token="secret",
            max_retries=3,
            timeout=30,
        )
        self.assertEqual(client.endpoint, "http://example.com/api")
        self.assertEqual(client.token, "secret")
        self.assertEqual(client.max_retries, 3)
        self.assertEqual(client.timeout, 30)
        self.assertIn("Authorization", client.headers)

    def test_client_no_token(self):
        """Test client without token."""
        client = APIClient(endpoint="http://example.com/api")
        self.assertIsNone(client.token)
        self.assertNotIn("Authorization", client.headers)

    def test_invalid_endpoint_protocol(self):
        """Test invalid endpoint protocol raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            APIClient(endpoint="file:///etc/passwd")
        self.assertIn("http:// or https://", str(ctx.exception))

    def test_https_endpoint(self):
        """Test HTTPS endpoint is accepted."""
        client = APIClient(endpoint="https://example.com/api")
        self.assertEqual(client.endpoint, "https://example.com/api")


class TestSyncExporter(unittest.TestCase):
    """Test sync exporter."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_exporter_creation(self):
        """Test exporter is created with correct values."""
        exporter = create_sync_exporter(
            endpoint="http://example.com/api",
            token="secret",
            backup_dir=self.temp_dir,
        )
        self.assertEqual(exporter.client.endpoint, "http://example.com/api")
        self.assertEqual(exporter.backup_dir, self.temp_dir)

    def test_backup_directory_created(self):
        """Test backup directory is created."""
        backup_dir = Path(self.temp_dir) / "backups"
        create_sync_exporter(
            endpoint="http://example.com/api",
            backup_dir=str(backup_dir),
        )
        self.assertTrue(backup_dir.exists())
        self.assertTrue(backup_dir.is_dir())

    def test_sync_error_dataclass(self):
        """Test SyncError structure."""
        error = SyncError(field="test", message="test message")
        self.assertEqual(error.field, "test")
        self.assertEqual(error.message, "test message")

    def test_create_backup(self):
        """Test local backup creation."""
        exporter = create_sync_exporter(
            endpoint="http://example.com/api",
            backup_dir=self.temp_dir,
        )
        channels = {"Channel1": {"url": "http://example.com"}}
        backup_path = exporter._create_backup(channels, "test_channels.json")

        self.assertIsNotNone(backup_path)
        self.assertTrue(Path(backup_path).exists())

        with open(backup_path) as f:
            saved = json.load(f)
        self.assertEqual(saved, channels)

    def test_sync_and_backup_failure(self):
        """Test sync then backup on failure."""
        exporter = create_sync_exporter(
            endpoint="http://127.0.0.1:1/api",
            backup_dir=self.temp_dir,
            max_retries=1,
            timeout=2,
        )
        channels = {"Channel1": {"url": "http://example.com"}}

        errors = exporter.sync_and_backup(channels, "test.json")

        self.assertEqual(len(errors), 2)
        self.assertEqual(errors[0].field, "api_sync")
        self.assertEqual(errors[1].field, "backup")

    def test_sync_and_backup_success(self):
        """Test sync succeeds (no backup needed)."""
        exporter = create_sync_exporter(
            endpoint="http://httpbin.org/post",
            backup_dir=self.temp_dir,
        )
        channels = {"TestChannel": {"url": "http://test.com"}}

        errors = exporter.sync_and_backup(channels, f"test_{id(self)}.json")

        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
