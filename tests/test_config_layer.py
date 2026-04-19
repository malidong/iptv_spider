import sys
import unittest

from src.iptv_spider.utils import build_effective_runtime_config, sanitize_runtime_config


class TestConfigLayer(unittest.TestCase):
    def test_env_overrides_defaults(self):
        config = build_effective_runtime_config(
            argv=[],
            environ={
                "IPTV_SPIDER_OUTPUT_DIR": "env-output",
                "IPTV_SPIDER_MAX_RETRIES": "7",
                "IPTV_SPIDER_CACHE_ENABLED": "false",
            },
        )

        self.assertEqual(config["output_dir"], "env-output")
        self.assertEqual(config["max_retries"], 7)
        self.assertFalse(config["cache_enabled"])

    def test_cli_overrides_env(self):
        config = build_effective_runtime_config(
            argv=[
                "--output_dir",
                "cli-output",
                "--max_retries",
                "11",
                "--cache_enabled",
            ],
            environ={
                "IPTV_SPIDER_OUTPUT_DIR": "env-output",
                "IPTV_SPIDER_MAX_RETRIES": "7",
                "IPTV_SPIDER_CACHE_ENABLED": "false",
            },
        )

        self.assertEqual(config["output_dir"], "cli-output")
        self.assertEqual(config["max_retries"], 11)
        self.assertTrue(config["cache_enabled"])

    def test_env_type_parsing_and_sanitization(self):
        config = build_effective_runtime_config(
            argv=[],
            environ={
                "IPTV_SPIDER_SPEED_THRESHOLD_MB": "0.75",
                "IPTV_SPIDER_REQUEST_TIMEOUT": "45",
                "IPTV_SPIDER_OUTPUT_WITH_EPG": "true",
                "IPTV_SPIDER_CACHE_CLEAR": "yes",
                "IPTV_SPIDER_CACHE_TTL_HOURS": "12",
                "IPTV_SPIDER_PROBE_TIMEOUT": "90",
            },
        )

        self.assertEqual(config["speed_threshold_mb"], 0.75)
        self.assertEqual(config["request_timeout"], 45)
        self.assertTrue(config["output_with_epg"])
        self.assertTrue(config["cache_clear"])
        self.assertEqual(config["cache_ttl_hours"], 12)
        self.assertEqual(config["probe_timeout"], 90)
        self.assertEqual(config["url_or_path"], config["m3u8_url"])

        sanitized = sanitize_runtime_config(
            {
                "url_or_path": "http://example.com/list.m3u",
                "access_token": "secret-value",
                "epg_url": "http://example.com/epg.xml",
            }
        )

        self.assertIn("url_or_path", sanitized)
        self.assertIn("epg_url", sanitized)
        self.assertNotIn("access_token", sanitized)

    def test_health_option_parsing(self):
        config = build_effective_runtime_config(argv=["--health"])
        self.assertTrue(config["health"])

        config = build_effective_runtime_config(argv=["--health", "--verbose"])
        self.assertTrue(config["health"])
        self.assertTrue(config["verbose"])

        config = build_effective_runtime_config(argv=[])
        self.assertFalse(config.get("health", False))


if __name__ == "__main__":
    unittest.main()
