# -*- coding: utf-8 -*-
"""Tests for template exporter."""

import unittest
from pathlib import Path
import tempfile

from iptv_spider.exporter import (
    ExportError,
    TemplateRenderer,
    _sanitize_service_name,
)


class TestSanitizeServiceName(unittest.TestCase):
    """Test service name sanitization."""

    def test_simple_name(self):
        self.assertEqual(_sanitize_service_name("CCTV-1"), "cctv-1")

    def test_spaces_underscores(self):
        self.assertEqual(_sanitize_service_name("CCTV 1"), "cctv_1")

    def test_special_chars(self):
        self.assertEqual(_sanitize_service_name("CCTV/1+2"), "cctv_1_2")

    def test_numbers(self):
        self.assertEqual(_sanitize_service_name("Channel 123"), "channel_123")


class TestTemplateRenderer(unittest.TestCase):
    """Test template renderer."""

    def setUp(self):
        self.renderer = TemplateRenderer()
        self.temp_dir = tempfile.mkdtemp()

    def test_render_docker_compose_basic(self):
        """Test basic docker-compose rendering."""
        channels = {
            "CCTV-1": {
                "media_url": "http://example.com/cctv1.m3u8",
                "resolution": "1080p",
                "fps": 30,
            },
            "CCTV-2": {
                "media_url": "http://example.com/cctv2.m3u8",
                "resolution": "720p",
                "fps": 25,
            },
        }
        output_path = str(Path(self.temp_dir) / "docker-compose.yml")

        errors = self.renderer.render_docker_compose(channels, output_path)

        self.assertEqual(errors, [])
        self.assertTrue(Path(output_path).exists())
        content = Path(output_path).read_text()
        self.assertIn("version: '3.8'", content)
        self.assertIn("cctv-1", content)
        self.assertIn("cctv-2", content)
        self.assertIn("http://example.com/cctv1.m3u8", content)

    def test_render_docker_compose_empty_channels(self):
        """Test rendering with no channels returns error."""
        errors = self.renderer.render_docker_compose({}, "/tmp/test.yml")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].field, "channels")

    def test_render_docker_compose_missing_url(self):
        """Test rendering with missing media_url returns error."""
        channels = {"CCTV-1": {"media_url": ""}}
        errors = self.renderer.render_docker_compose(channels, "/tmp/test.yml")
        self.assertTrue(any(e.field == "media_url" for e in errors))

    def test_render_custom_template(self):
        """Test custom template rendering."""
        template = "{{channel_name}}: {{media_url}}\n"
        channels = {
            "Test": {"media_url": "http://test.com", "resolution": "", "fps": ""}
        }
        output_path = str(Path(self.temp_dir) / "output.txt")

        errors = self.renderer.render_custom(template, channels, output_path)

        self.assertEqual(errors, [])
        content = Path(output_path).read_text()
        self.assertIn("Test", content)
        self.assertIn("http://test.com", content)

    def test_render_custom_empty_template(self):
        """Test rendering with empty template returns error."""
        errors = self.renderer.render_custom("", {}, "/tmp/test.yml")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].field, "template")

    def test_export_error_dataclass(self):
        """Test ExportError structure."""
        error = ExportError(field="test", message="test message")
        self.assertEqual(error.field, "test")
        self.assertEqual(error.message, "test message")


class TestDockerComposeOutput(unittest.TestCase):
    """Test docker-compose output format."""

    def setUp(self):
        self.renderer = TemplateRenderer()
        self.temp_dir = tempfile.mkdtemp()

    def test_output_is_valid_yaml_structure(self):
        """Test output has valid docker-compose structure."""
        channels = {"Test-Channel": {"media_url": "http://test.com/stream"}}
        output_path = str(Path(self.temp_dir) / "docker-compose.yml")

        self.renderer.render_docker_compose(channels, output_path)

        content = Path(output_path).read_text()
        self.assertTrue(content.startswith("version:"))
        self.assertIn("services:", content)
        self.assertIn("test-channel:", content)
        self.assertIn("image:", content)
        self.assertIn("environment:", content)
        self.assertIn("restart:", content)

    def test_multiple_channels(self):
        """Test rendering multiple channels."""
        channels = {
            f"Channel-{i}": {"media_url": f"http://example.com/{i}"} for i in range(5)
        }
        output_path = str(Path(self.temp_dir) / "docker-compose.yml")

        self.renderer.render_docker_compose(channels, output_path)

        content = Path(output_path).read_text()
        for i in range(5):
            self.assertIn(f"channel-{i}:", content)


if __name__ == "__main__":
    unittest.main()
