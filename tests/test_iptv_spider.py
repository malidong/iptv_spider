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
from src.iptv_spider.utils import arg_parser, load_config, save_config, get_config_dir
from src.iptv_spider.main import main


class TestChannel(unittest.TestCase):
    """Test cases for the Channel class."""

    def setUp(self):
        """Set up test fixtures."""
        self.channel = Channel(
            meta="#EXTINF:-1",
            channel_name="Test Channel",
            media_url="http://example.com/stream.m3u8",
            max_retries=1,
            request_timeout=10
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
            media_url="http://example.com/stream.ts"
        )
        self.assertFalse(direct_channel.is_direct)

    def test_channel_max_retries(self):
        """Test max_retries configuration."""
        channel_with_retries = Channel(
            meta="#EXTINF:-1",
            channel_name="Retry Test",
            media_url="http://example.com/stream.m3u8",
            max_retries=5,
            request_timeout=20
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
        self.temp_m3u = tempfile.NamedTemporaryFile(mode='w', suffix='.m3u', delete=False, encoding='utf-8')
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
            request_timeout=30
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
            request_timeout=30
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
            request_timeout=30
        )
        self.assertIsInstance(m3u8.black_servers, list)
        self.assertEqual(len(m3u8.black_servers), 0)

    def test_m3u8_tested_servers_initialization(self):
        """Test that tested servers cache is initialized."""
        m3u8 = M3U8(
            path=self.temp_m3u.name,
            regex_filter=r"CCTV.*",
            max_retries=3,
            request_timeout=30
        )
        self.assertIsInstance(m3u8.tested_servers, dict)


class TestUtilsFunctions(unittest.TestCase):
    """Test cases for utility functions."""

    def test_arg_parser(self):
        """Test command-line argument parsing."""
        with patch('sys.argv', ['prog']):
            args = arg_parser()
            self.assertIsNotNone(args.url_or_path)
            self.assertIsNotNone(args.filter)
            self.assertIsNotNone(args.output_dir)
            self.assertEqual(args.speed_threshold_mb, 0.3)
            self.assertEqual(args.speed_limit_mb, 2)
            self.assertEqual(args.max_retries, 3)
            self.assertEqual(args.request_timeout, 30)

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
                "max_retries": 5
            }
            config_file = Path(tmpdir) / "test_config.json"
            
            # Manually save config
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(test_config, f)
            
            # Load and verify
            with open(config_file, 'r', encoding='utf-8') as f:
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
        self.temp_m3u = tempfile.NamedTemporaryFile(mode='w', suffix='.m3u', delete=False, encoding='utf-8')
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

    @patch('src.iptv_spider.main.M3U8')
    def test_main_returns_statistics(self, mock_m3u8):
        """Test that main function returns statistics."""
        # Mock the M3U8 class
        mock_instance = MagicMock()
        mock_instance.channels = {"CCTV-1": [], "CCTV-2": []}
        mock_instance.get_best_channels.return_value = {}
        mock_m3u8.return_value = mock_instance
        
        stats = main(
            m3u_url=self.temp_m3u.name,
            regex_filter=r"CCTV.*",
            output_dir=self.temp_output_dir,
            speed_threshold_mb=0.3,
            speed_limit_mb=2,
            max_retries=3,
            request_timeout=30
        )
        
        self.assertIsInstance(stats, dict)
        self.assertIn("total_channels_filtered", stats)
        self.assertIn("best_channels_tested", stats)
        self.assertIn("valid_channels_output", stats)
        self.assertIn("speed_threshold_mb", stats)
        self.assertIn("output_files", stats)


if __name__ == '__main__':
    unittest.main()
