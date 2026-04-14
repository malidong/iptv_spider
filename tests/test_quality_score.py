# -*- coding: utf-8 -*-
"""
Unit tests for the Quality Score module.

Tests cover scoring calculations, boundary conditions, and ranking behavior.
"""

import unittest
from dataclasses import dataclass, field
from typing import Optional

from src.iptv_spider.quality_score import (
    QualityScoreEngine,
    ScoreProfile,
    QualityScore,
    RESOLUTION_PATTERNS,
)


@dataclass
class MockChannel:
    """Mock Channel object for testing."""

    channel_name: str
    media_url: str
    speed: float = -1
    resolution: str = "Unknown"
    fps: float = -1.0
    startup_latency: float = -1.0


class TestResolutionParsing(unittest.TestCase):
    """Test cases for resolution parsing."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = QualityScoreEngine()

    def test_known_resolutions(self):
        """Test mapping of known resolutions to tiers."""
        for res, tier in RESOLUTION_PATTERNS.items():
            score = self.engine._parse_resolution(res)
            self.assertEqual(score, tier, f"Failed for {res}")

    def test_unknown_resolution(self):
        """Test handling of unknown resolution."""
        self.assertEqual(self.engine._parse_resolution("Unknown"), 0)
        self.assertEqual(self.engine._parse_resolution(""), 0)
        self.assertEqual(self.engine._parse_resolution("abc"), 0)

    def test_invalid_resolution_format(self):
        """Test handling of invalid resolution format."""
        self.assertEqual(self.engine._parse_resolution("1920"), 0)
        self.assertEqual(self.engine._parse_resolution("x1080"), 0)


class TestAvailabilityScore(unittest.TestCase):
    """Test cases for availability scoring."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = QualityScoreEngine()

    def test_available_channel(self):
        """Test score for available channel."""
        score = self.engine._calculate_availability_score(1000)
        self.assertEqual(score, 100.0)

    def test_unavailable_channel(self):
        """Test score for unavailable channel."""
        score = self.engine._calculate_availability_score(0)
        self.assertEqual(score, 0.0)

    def test_negative_speed(self):
        """Test score for negative speed."""
        score = self.engine._calculate_availability_score(-1)
        self.assertEqual(score, 0.0)


class TestLatencyScore(unittest.TestCase):
    """Test cases for latency scoring."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = QualityScoreEngine()

    def test_zero_latency(self):
        """Test score for zero latency."""
        score = self.engine._calculate_latency_score(0)
        self.assertEqual(score, 100.0)

    def test_under_max_latency(self):
        """Test score for latency under max."""
        profile = ScoreProfile(max_latency_ms=5000, latency_penalty_per_ms=0.5)
        engine = QualityScoreEngine(profile)
        score = engine._calculate_latency_score(1000)
        self.assertEqual(score, 100.0 - 1000 * 0.5)

    def test_at_max_latency(self):
        """Test score at maximum latency boundary."""
        profile = ScoreProfile(max_latency_ms=5000)
        engine = QualityScoreEngine(profile)
        score = engine._calculate_latency_score(5000)
        self.assertEqual(score, 0.0)

    def test_over_max_latency(self):
        """Test score over maximum latency."""
        profile = ScoreProfile(max_latency_ms=5000)
        engine = QualityScoreEngine(profile)
        score = engine._calculate_latency_score(6000)
        self.assertEqual(score, 0.0)

    def test_negative_latency(self):
        """Test score for negative latency."""
        score = self.engine._calculate_latency_score(-1)
        self.assertEqual(score, 0.0)


class TestResolutionScore(unittest.TestCase):
    """Test cases for resolution scoring."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = QualityScoreEngine()

    def test_hd_resolution(self):
        """Test score for HD resolution."""
        score = self.engine._calculate_resolution_score("1920x1080")
        self.assertEqual(score, 62.5)

    def test_sd_resolution(self):
        """Test score for SD resolution."""
        score = self.engine._calculate_resolution_score("854x480")
        self.assertEqual(score, 37.5)

    def test_unknown_resolution(self):
        """Test score for unknown resolution."""
        score = self.engine._calculate_resolution_score("Unknown")
        self.assertEqual(score, 0.0)


class TestFpsScore(unittest.TestCase):
    """Test cases for FPS scoring."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = QualityScoreEngine()

    def test_high_fps(self):
        """Test score for high FPS."""
        self.assertEqual(self.engine._calculate_fps_score(60), 100.0)
        self.assertEqual(self.engine._calculate_fps_score(120), 100.0)

    def test_medium_fps(self):
        """Test score for medium FPS."""
        self.assertEqual(self.engine._calculate_fps_score(50), 85.0)
        self.assertEqual(self.engine._calculate_fps_score(30), 60.0)

    def test_cinema_fps(self):
        """Test score for cinema FPS."""
        self.assertEqual(self.engine._calculate_fps_score(24), 40.0)

    def test_low_fps(self):
        """Test score for low FPS."""
        self.assertEqual(self.engine._calculate_fps_score(15), 20.0)

    def test_negative_fps(self):
        """Test score for negative FPS."""
        self.assertEqual(self.engine._calculate_fps_score(-1), 0.0)


class TestCalculateScore(unittest.TestCase):
    """Test cases for calculate_score method."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = QualityScoreEngine()
        self.profile = ScoreProfile(
            availability_weight=40,
            latency_weight=20,
            resolution_weight=25,
            fps_weight=15,
        )
        self.engine_with_profile = QualityScoreEngine(self.profile)

    def test_full_channel(self):
        """Test score for fully populated channel."""
        channel = MockChannel(
            channel_name="Test",
            media_url="http://example.com/stream.m3u8",
            speed=1000000,
            resolution="1920x1080",
            fps=60.0,
            startup_latency=500,
        )
        score = self.engine.calculate_score(channel)

        self.assertGreater(score.total_score, 0)
        self.assertTrue(score.is_available)
        self.assertEqual(score.resolution, "1920x1080")
        self.assertEqual(score.fps, 60.0)

    def test_unavailable_channel(self):
        """Test score for unavailable channel."""
        channel = MockChannel(
            channel_name="Test",
            media_url="http://example.com/stream.m3u8",
            speed=0,
            resolution="Unknown",
            fps=-1.0,
        )
        score = self.engine.calculate_score(channel)

        self.assertEqual(score.total_score, 0)
        self.assertFalse(score.is_available)
        self.assertEqual(score.availability_score, 0.0)

    def test_explicit_latency(self):
        """Test with explicit latency parameter."""
        channel = MockChannel(
            channel_name="Test",
            media_url="http://example.com/stream.m3u8",
            speed=1000000,
        )
        score = self.engine.calculate_score(channel, latency_ms=1000)
        self.assertEqual(score.latency_ms, 1000)

    def test_weighting_behavior(self):
        """Test that weighting affects total score."""
        channel = MockChannel(
            channel_name="Test",
            media_url="http://example.com/stream.m3u8",
            speed=1000000,
            resolution="1920x1080",
            fps=60.0,
        )
        score_default = self.engine.calculate_score(channel)
        score_custom = self.engine_with_profile.calculate_score(channel)

        self.assertNotEqual(score_default.total_score, score_custom.total_score)


class TestRankChannels(unittest.TestCase):
    """Test cases for rank_channels method."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = QualityScoreEngine()

    def test_ranking_order(self):
        """Test that ranking orders by score descending."""
        channels = [
            MockChannel("C", "http://c.com", speed=1000, resolution="640x360"),
            MockChannel("A", "http://a.com", speed=1000000, resolution="1920x1080"),
            MockChannel("B", "http://b.com", speed=100000, resolution="1280x720"),
        ]
        ranked = self.engine.rank_channels(channels)

        self.assertEqual(ranked[0][0].channel_name, "A")
        self.assertEqual(ranked[1][0].channel_name, "B")
        self.assertEqual(ranked[2][0].channel_name, "C")

    def test_stable_ranking(self):
        """Test stable ranking for equal scores."""
        channels = [
            MockChannel("A1", "http://a1.com", speed=0),
            MockChannel("A2", "http://a2.com", speed=0),
        ]
        ranked = self.engine.rank_channels(channels)
        self.assertEqual(len(ranked), 2)

    def test_empty_list(self):
        """Test ranking empty list."""
        ranked = self.engine.rank_channels([])
        self.assertEqual(ranked, [])


class TestScoreProfile(unittest.TestCase):
    """Test cases for ScoreProfile."""

    def test_default_weights(self):
        """Test default weight values."""
        profile = ScoreProfile()
        self.assertEqual(profile.availability_weight, 40.0)
        self.assertEqual(profile.latency_weight, 20.0)
        self.assertEqual(profile.resolution_weight, 25.0)
        self.assertEqual(profile.fps_weight, 15.0)

    def test_custom_weights(self):
        """Test custom weight values."""
        profile = ScoreProfile(
            availability_weight=50,
            latency_weight=10,
            resolution_weight=30,
            fps_weight=10,
        )
        self.assertEqual(profile.availability_weight, 50)
        self.assertEqual(profile.latency_weight, 10)
        self.assertEqual(profile.resolution_weight, 30)
        self.assertEqual(profile.fps_weight, 10)


class TestQualityScoreExport(unittest.TestCase):
    """Test cases for QualityScore export."""

    def test_to_dict(self):
        """Test dictionary export."""
        score = QualityScore(
            total_score=85.5,
            availability_score=100.0,
            latency_score=80.0,
            resolution_score=75.0,
            fps_score=100.0,
            is_available=True,
            latency_ms=500.0,
            resolution="1920x1080",
            fps=60.0,
        )
        d = score.to_dict()

        self.assertEqual(d["total_score"], 85.5)
        self.assertEqual(d["availability_score"], 100.0)
        self.assertTrue(d["is_available"])


if __name__ == "__main__":
    unittest.main()
