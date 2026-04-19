# -*- coding: utf-8 -*-
"""
Unit tests for the IPTV Spider project.

Tests cover M3U8 file parsing, Channel speed testing, and utility functions.
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.iptv_spider.m3u import M3U8
from src.iptv_spider.channel import Channel
from src.iptv_spider.utils import arg_parser, get_config_dir, url_fingerprint
from src.iptv_spider.main import main, RunStats


class TestChannel(unittest.TestCase):
    """Test cases for the Channel class."""

    def setUp(self):
        """Set up test fixtures."""
        self.channel = Channel(
            meta="#EXTINF:-1",
            channel_name="Test Channel",
            media_url="http://example.com/stream.m3u8",
            max_retries=1,
            request_timeout=10,
        )

    def test_channel_initialization(self):
        """Test Channel object initialization."""
        self.assertEqual(self.channel.channel_name, "Test Channel")
        self.assertEqual(self.channel.media_url, "http://example.com/stream.m3u8")
        self.assertTrue(self.channel.is_direct)
        self.assertEqual(self.channel.speed, -1)
        self.assertEqual(self.channel.resolution, "Unknown")

    def test_channel_direct_detection(self):
        """Test detection of direct vs M3U8 streams."""
        direct_channel = Channel(
            meta="#EXTINF:-1",
            channel_name="Direct Stream",
            media_url="http://example.com/stream.ts",
        )
        self.assertFalse(direct_channel.is_direct)

    def test_channel_max_retries(self):
        """Test max_retries configuration."""
        channel_with_retries = Channel(
            meta="#EXTINF:-1",
            channel_name="Retry Test",
            media_url="http://example.com/stream.m3u8",
            max_retries=5,
            request_timeout=20,
        )
        self.assertEqual(channel_with_retries.max_retries, 5)
        self.assertEqual(channel_with_retries.request_timeout, 20)


class TestM3U8(unittest.TestCase):
    """Test cases for the M3U8 class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_m3u_content = """#EXTM3U
#EXTINF:-1 tvg-name="CCTV1" tvg-logo="http://example.com/logo.png",CCTV-1
http://example.com/cctv1.m3u8
#EXTINF:-1 tvg-name="CCTV2",CCTV-2
http://example.com/cctv2.m3u8
#EXTINF:-1 tvg-name="HBO",HBO
udp://example.com/hbo
"""
        # Create a temporary M3U file
        self.temp_m3u = tempfile.NamedTemporaryFile(
            mode="w", suffix=".m3u", delete=False, encoding="utf-8"
        )
        self.temp_m3u.write(self.test_m3u_content)
        self.temp_m3u.close()

    def tearDown(self):
        """Clean up test fixtures."""
        import os

        if os.path.exists(self.temp_m3u.name):
            os.unlink(self.temp_m3u.name)

    def test_m3u8_initialization(self):
        """Test M3U8 object initialization."""
        m3u8 = M3U8(
            path=self.temp_m3u.name,
            regex_filter=r"CCTV.*",
            max_retries=3,
            request_timeout=30,
        )
        self.assertEqual(len(m3u8.channels), 2)  # CCTV-1 and CCTV-2, HBO filtered out
        self.assertIn("CCTV-1", m3u8.channels)
        self.assertIn("CCTV-2", m3u8.channels)

    def test_m3u8_filters_udp_streams(self):
        """Test that UDP streams are filtered out."""
        m3u8 = M3U8(
            path=self.temp_m3u.name,
            regex_filter=r".*",
            max_retries=3,
            request_timeout=30,
        )
        # UDP stream should not be loaded
        for channels in m3u8.channels.values():
            for channel in channels:
                self.assertNotIn("udp://", channel.media_url)

    def test_m3u8_black_servers_initialization(self):
        """Test that black servers list is initialized."""
        m3u8 = M3U8(
            path=self.temp_m3u.name,
            regex_filter=r"CCTV.*",
            max_retries=3,
            request_timeout=30,
        )
        self.assertIsInstance(m3u8.black_servers, list)
        self.assertEqual(len(m3u8.black_servers), 0)

    def test_m3u8_tested_servers_initialization(self):
        """Test that tested servers cache is initialized."""
        m3u8 = M3U8(
            path=self.temp_m3u.name,
            regex_filter=r"CCTV.*",
            max_retries=3,
            request_timeout=30,
        )
        self.assertIsInstance(m3u8.tested_servers, dict)

    def test_m3u8_dedup_by_url_fingerprint(self):
        """Test deduplication by URL fingerprint within a channel name."""
        content = """#EXTM3U
#EXTINF:-1 tvg-name="CCTV1",CCTV-1
http://example.com/cctv1.m3u8?b=2&a=1
#EXTINF:-1 tvg-name="CCTV1",CCTV-1
http://example.com/cctv1.m3u8?a=1&b=2
"""
        temp_m3u = tempfile.NamedTemporaryFile(
            mode="w", suffix=".m3u", delete=False, encoding="utf-8"
        )
        temp_m3u.write(content)
        temp_m3u.close()
        try:
            m3u8 = M3U8(
                path=temp_m3u.name,
                regex_filter=r".*",
                max_retries=1,
                request_timeout=10,
                dedup_mode="url_fingerprint",
            )
            self.assertEqual(len(m3u8.channels["CCTV-1"]), 1)
        finally:
            import os

            if os.path.exists(temp_m3u.name):
                os.unlink(temp_m3u.name)

    def test_m3u8_dedup_trace(self):
        """Test that dedup_trace is populated with deduplication reasons."""
        content = """#EXTM3U
#EXTINF:-1 tvg-name="CCTV1",CCTV-1
http://example.com/cctv1.m3u8
#EXTINF:-1 tvg-name="CCTV1",CCTV-1
http://example.com/cctv1.m3u8
#EXTINF:-1 tvg-name="CCTV1",CCTV-1
http://example.com/cctv1.m3u8?a=1&b=2
#EXTINF:-1 tvg-name="CCTV2",CCTV-2
http://example.com/cctv2.m3u8
"""
        temp_m3u = tempfile.NamedTemporaryFile(
            mode="w", suffix=".m3u", delete=False, encoding="utf-8"
        )
        temp_m3u.write(content)
        temp_m3u.close()
        try:
            m3u8 = M3U8(
                path=temp_m3u.name,
                regex_filter=r".*",
                max_retries=1,
                request_timeout=10,
                dedup_mode="url_fingerprint",
            )
            self.assertIsInstance(m3u8.dedup_trace, list)
            self.assertGreater(len(m3u8.dedup_trace), 0)
            for entry in m3u8.dedup_trace:
                self.assertIn("channel_name", entry)
                self.assertIn("media_url", entry)
                self.assertIn("fingerprint", entry)
                self.assertIn("action", entry)
                self.assertIn("reason", entry)
        finally:
            import os

            if os.path.exists(temp_m3u.name):
                os.unlink(temp_m3u.name)

    def test_m3u8_uses_speed_cache(self):
        """Test that speed cache avoids re-testing when within TTL."""
        content = """#EXTM3U
#EXTINF:-1 tvg-name="CCTV1",CCTV-1
http://example.com/cctv1.m3u8
"""
        temp_m3u = tempfile.NamedTemporaryFile(
            mode="w", suffix=".m3u", delete=False, encoding="utf-8"
        )
        temp_m3u.write(content)
        temp_m3u.close()
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = Path(tmpdir) / "tested_channels.json"
            fp = url_fingerprint("http://example.com/cctv1.m3u8")
            cache_payload = {
                fp: {
                    "speed": 123456.0,
                    "resolution": "1280x720",
                    "last_tested": "2099-01-01T00:00:00+00:00",
                    "media_url": "http://example.com/cctv1.m3u8",
                    "channel_name": "CCTV-1",
                }
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_payload, f)
            try:
                m3u8 = M3U8(
                    path=temp_m3u.name,
                    regex_filter=r".*",
                    max_retries=1,
                    request_timeout=10,
                    cache_enabled=True,
                    cache_ttl_hours=24,
                    cache_file=str(cache_file),
                )
                with patch(
                    "src.iptv_spider.channel.Channel.get_speed"
                ) as mock_get_speed:
                    best = m3u8.get_best_channels()
                    mock_get_speed.assert_not_called()
                self.assertIn("CCTV-1", best)
                self.assertEqual(best["CCTV-1"].speed, 123456.0)
            finally:
                import os

                if os.path.exists(temp_m3u.name):
                    os.unlink(temp_m3u.name)

    def test_m3u8_cache_clear(self):
        """Test clearing cache via cache_clear flag."""
        content = """#EXTM3U
#EXTINF:-1 tvg-name="CCTV1",CCTV-1
http://example.com/cctv1.m3u8
"""
        temp_m3u = tempfile.NamedTemporaryFile(
            mode="w", suffix=".m3u", delete=False, encoding="utf-8"
        )
        temp_m3u.write(content)
        temp_m3u.close()
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = Path(tmpdir) / "tested_channels.json"
            fp = url_fingerprint("http://example.com/cctv1.m3u8")
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(
                    {fp: {"speed": 1, "last_tested": "2099-01-01T00:00:00+00:00"}}, f
                )
            try:
                m3u8 = M3U8(
                    path=temp_m3u.name,
                    regex_filter=r".*",
                    max_retries=1,
                    request_timeout=10,
                    cache_enabled=True,
                    cache_clear=True,
                    cache_file=str(cache_file),
                )
                self.assertEqual(m3u8.tested_channels, {})
                with open(cache_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self.assertEqual(saved, {})
            finally:
                import os

                if os.path.exists(temp_m3u.name):
                    os.unlink(temp_m3u.name)


class TestUtilsFunctions(unittest.TestCase):
    """Test cases for utility functions."""

    def test_arg_parser(self):
        """Test command-line argument parsing."""
        with patch("sys.argv", ["prog"]):
            args = arg_parser()
            self.assertIsNotNone(args.url_or_path)
            self.assertIsNotNone(args.filter)
            self.assertIsNotNone(args.output_dir)
            self.assertEqual(args.speed_threshold_mb, 0.3)
            self.assertEqual(args.speed_limit_mb, 2)
            self.assertEqual(args.max_retries, 3)
            self.assertEqual(args.request_timeout, 30)
            self.assertEqual(args.epg_url, "http://epg.51zmt.top:8000/e.xml")
            self.assertFalse(args.output_with_epg)
            self.assertEqual(args.dedup_mode, "url_fingerprint")
            self.assertEqual(args.dedup_keep, "first")
            self.assertTrue(args.cache_enabled)
            self.assertEqual(args.cache_ttl_hours, 24)
            self.assertFalse(args.cache_clear)

    def test_get_config_dir(self):
        """Test configuration directory retrieval."""
        config_dir = get_config_dir()
        self.assertIsInstance(config_dir, Path)
        self.assertTrue(config_dir.exists())

    def test_save_and_load_config(self):
        """Test configuration save and load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_config = {
                "test_key": "test_value",
                "speed_threshold_mb": 0.5,
                "max_retries": 5,
            }
            config_file = Path(tmpdir) / "test_config.json"

            # Manually save config
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(test_config, f)

            # Load and verify
            with open(config_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            self.assertEqual(loaded["test_key"], "test_value")
            self.assertEqual(loaded["speed_threshold_mb"], 0.5)
            self.assertEqual(loaded["max_retries"], 5)


class TestMainFunction(unittest.TestCase):
    """Test cases for the main function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_m3u_content = """#EXTM3U
#EXTINF:-1 tvg-name="CCTV1",CCTV-1
http://example.com/cctv1.m3u8
#EXTINF:-1 tvg-name="CCTV2",CCTV-2
http://example.com/cctv2.m3u8
"""
        self.temp_m3u = tempfile.NamedTemporaryFile(
            mode="w", suffix=".m3u", delete=False, encoding="utf-8"
        )
        self.temp_m3u.write(self.test_m3u_content)
        self.temp_m3u.close()

        self.temp_output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import os
        import shutil

        if os.path.exists(self.temp_m3u.name):
            os.unlink(self.temp_m3u.name)
        if os.path.exists(self.temp_output_dir):
            shutil.rmtree(self.temp_output_dir)

    @patch("src.iptv_spider.main.M3U8")
    def test_main_returns_statistics(self, mock_m3u8):
        """Test that main function returns statistics."""
        # Mock the M3U8 class
        mock_instance = MagicMock()
        mock_instance.channels = {"CCTV-1": [], "CCTV-2": []}
        mock_instance.get_best_channels.return_value = {}
        mock_instance.dedup_trace = []
        mock_m3u8.return_value = mock_instance

        stats = main(
            m3u_url=self.temp_m3u.name,
            regex_filter=r"CCTV.*",
            output_dir=self.temp_output_dir,
            speed_threshold_mb=0.3,
            speed_limit_mb=2,
            max_retries=3,
            request_timeout=30,
        )

        self.assertIsInstance(stats, RunStats)
        self.assertEqual(stats.total_channels_filtered, 2)
        self.assertEqual(stats.best_channels_tested, 0)
        self.assertEqual(stats.valid_channels_output, 0)
        self.assertEqual(stats.speed_threshold_mb, 0.3)
        self.assertEqual(stats.deduplicated_count, 0)

    @patch("src.iptv_spider.main.M3U8")
    def test_main_writes_epg_header(self, mock_m3u8):
        """Test that M3U output includes EPG header when enabled."""
        mock_instance = MagicMock()
        channel = MagicMock()
        channel.channel_name = "CCTV-1"
        channel.meta = '#EXTINF:-1 tvg-name="CCTV1"'
        channel.media_url = "http://example.com/cctv1.m3u8"
        channel.speed = 1000000
        channel.resolution = "1920x1080"
        mock_instance.channels = {"CCTV-1": []}
        mock_instance.get_best_channels.return_value = {"CCTV-1": channel}
        mock_m3u8.return_value = mock_instance

        output_dir = tempfile.mkdtemp()
        try:
            main(
                m3u_url=self.temp_m3u.name,
                regex_filter=r"CCTV.*",
                output_dir=output_dir,
                speed_threshold_mb=0.0,
                speed_limit_mb=2,
                max_retries=1,
                request_timeout=10,
                epg_url="http://example.com/epg.xml",
                output_with_epg=True,
            )
            m3u_path = Path(output_dir) / "best_channels.m3u"
            with open(m3u_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
            self.assertEqual(first_line, '#EXTM3U url-tvg="http://example.com/epg.xml"')
        finally:
            import shutil

            if Path(output_dir).exists():
                shutil.rmtree(output_dir)


if __name__ == "__main__":
    unittest.main()


class TestDedupKeepValidation(unittest.TestCase):
    """Test cases for dedup_keep parameter validation."""

    def test_invalid_dedup_keep_raises_error(self):
        """Test that invalid dedup_keep value raises ValueError."""
        from src.iptv_spider.m3u import M3U8

        with tempfile.NamedTemporaryFile(mode="w", suffix=".m3u", delete=False) as f:
            f.write("#EXTM3U\n#EXTINF:-1,Test\nhttp://example.com/test.m3u\n")
            temp_file = f.name
        try:
            with self.assertRaises(ValueError) as context:
                M3U8(path=temp_file, regex_filter=".*", dedup_keep="invalid")
            self.assertIn("Invalid dedup_keep value", str(context.exception))
            self.assertIn("first", str(context.exception))
            self.assertIn("fastest", str(context.exception))
        finally:
            Path(temp_file).unlink()
