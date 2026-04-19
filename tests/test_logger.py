# -*- coding: utf-8 -*-
"""
Unit tests for logger module.
"""

from unittest import TestCase
from unittest.mock import patch

from iptv_spider.logger import create_run_id, log_structured, log_event


class TestCreateRunId(TestCase):
    def test_create_run_id_returns_8_char_string(self):
        run_id = create_run_id()
        self.assertEqual(len(run_id), 8)

    def test_create_run_id_is_hex(self):
        run_id = create_run_id()
        for char in run_id:
            self.assertIn(char, "0123456789abcdef")


class TestLogStructured(TestCase):
    @patch("iptv_spider.logger.logger")
    def test_log_structured_with_all_fields(self, mock_logger):
        log_structured(
            level=20,
            message="Test message",
            run_id="abc12345",
            stage="probe",
            source="m3u8",
            latency_ms=150.5,
        )
        mock_logger.log.assert_called_once()

    @patch("iptv_spider.logger.logger")
    def test_log_structured_with_minimal_fields(self, mock_logger):
        log_structured(level=20, message="Minimal message")
        mock_logger.log.assert_called_once()


class TestLogEvent(TestCase):
    @patch("iptv_spider.logger.logger")
    def test_log_event_basic(self, mock_logger):
        log_event(event="run_start", run_id="abc12345", stage="init")
        mock_logger.info.assert_called_once()

    @patch("iptv_spider.logger.logger")
    def test_log_event_with_status(self, mock_logger):
        log_event(event="run_end", run_id="abc12345", status="success")
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("run_end", call_args)
        self.assertIn("success", call_args)
