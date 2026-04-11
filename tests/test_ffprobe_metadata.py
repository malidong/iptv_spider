# -*- coding: utf-8 -*-
"""
Focused tests for ffprobe metadata extraction and export wiring.
"""

import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch
import subprocess

from src.iptv_spider.channel import Channel
from src.iptv_spider.main import main


class TestFFprobeMetadata(TestCase):
    def setUp(self):
        self.channel = Channel(
            meta="#EXTINF:-1",
            channel_name="Test Channel",
            media_url="http://example.com/stream.m3u8",
            max_retries=1,
            request_timeout=10,
            probe_timeout=5,
        )

    @patch("src.iptv_spider.channel.subprocess.run")
    def test_ffprobe_metadata_success_is_cached(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            {
                "streams": [
                    {
                        "width": 1920,
                        "height": 1080,
                        "avg_frame_rate": "30000/1001",
                        "r_frame_rate": "30/1",
                    }
                ]
            }
        )
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        metadata = self.channel.get_ffprobe_metadata()
        cached = self.channel.get_ffprobe_metadata()

        self.assertEqual(metadata["resolution"], "1920x1080")
        self.assertAlmostEqual(metadata["fps"], 30000 / 1001, places=3)
        self.assertEqual(cached, metadata)
        mock_run.assert_called_once()
        self.assertEqual(self.channel.resolution, "1920x1080")
        self.assertAlmostEqual(self.channel.fps, 30000 / 1001, places=3)

    @patch("src.iptv_spider.channel.subprocess.run")
    def test_ffprobe_metadata_timeout_returns_safe_defaults(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffprobe", timeout=5)

        metadata = self.channel.get_ffprobe_metadata()

        self.assertEqual(metadata["resolution"], "Unknown")
        self.assertEqual(metadata["fps"], -1.0)
        self.assertEqual(self.channel.resolution, "Unknown")
        self.assertEqual(self.channel.fps, -1.0)

    @patch("src.iptv_spider.main.M3U8")
    @patch("src.iptv_spider.channel.subprocess.run")
    def test_main_exports_ffprobe_metadata(self, mock_run, mock_m3u8):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            {
                "streams": [
                    {
                        "width": 1280,
                        "height": 720,
                        "avg_frame_rate": "25/1",
                        "r_frame_rate": "25/1",
                    }
                ]
            }
        )
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        channel = Channel(
            meta="#EXTINF:-1 tvg-name=\"Test\"",
            channel_name="Test Channel",
            media_url="http://example.com/stream.m3u8",
            max_retries=1,
            request_timeout=10,
            probe_timeout=5,
        )
        channel.speed = 2 * 1024 * 1024

        mock_instance = MagicMock()
        mock_instance.channels = {"Test Channel": [channel]}
        mock_instance.get_best_channels.return_value = {"Test Channel": channel}
        mock_m3u8.return_value = mock_instance

        output_dir = Path.cwd() / "_ffprobe_test_output"
        output_dir.mkdir(exist_ok=True)
        stats = main(
            m3u_url="http://example.com/test.m3u",
            regex_filter=r".*",
            output_dir=str(output_dir),
            speed_threshold_mb=0.1,
            speed_limit_mb=2,
            max_retries=1,
            request_timeout=10,
        )

        json_path = Path(stats["output_files"][0])
        with open(json_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        self.assertIn("Test Channel", payload)
        self.assertEqual(payload["Test Channel"]["resolution"], "1280x720")
        self.assertEqual(payload["Test Channel"]["fps"], 25.0)
        self.assertEqual(
            payload["Test Channel"]["video_metadata"],
            {"resolution": "1280x720", "fps": 25.0},
        )
        self.assertEqual(mock_run.call_count, 1)
        for path in output_dir.glob("*"):
            path.unlink(missing_ok=True)
