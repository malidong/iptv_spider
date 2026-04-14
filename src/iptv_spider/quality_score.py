# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
"""
Quality Score Module - Rule-based ranking for IPTV channel quality.

This module provides deterministic ranking for channel quality based on:
- Availability (channel is reachable)
- Startup latency (time to first byte)
- Resolution (video resolution)
- FPS (frames per second)

Typical usage:
    from iptv_spider.quality_score import QualityScoreEngine, ScoreProfile

    profile = ScoreProfile()
    engine = QualityScoreEngine(profile)
    score = engine.calculate_score(channel)
    ranked = engine.rank_channels([channel1, channel2])
"""

from dataclasses import dataclass, field
from typing import Optional
import re


RESOLUTION_PATTERNS = {
    "4320x2160": 8,
    "3840x2160": 7,
    "2560x1440": 6,
    "1920x1080": 5,
    "1280x720": 4,
    "854x480": 3,
    "640x360": 2,
    "426x240": 1,
}


@dataclass
class ScoreProfile:
    """
    Configuration for quality score weighting.

    Attributes:
        availability_weight: Weight for availability (default: 40)
        latency_weight: Weight for startup latency (default: 20)
        resolution_weight: Weight for resolution (default: 25)
        fps_weight: Weight for FPS (default: 15)
        latency_penalty_per_ms: Penalty per ms over target latency (default: 0.5)
        max_latency_ms: Maximum acceptable latency in ms (default: 5000)
    """

    availability_weight: float = 40.0
    latency_weight: float = 20.0
    resolution_weight: float = 25.0
    fps_weight: float = 15.0
    latency_penalty_per_ms: float = 0.5
    max_latency_ms: float = 5000.0


@dataclass
class QualityScore:
    """
    Quality score result with breakdown.

    Attributes:
        total_score: Total weighted score (0-100)
        availability_score: Score for availability (0-100)
        latency_score: Score for startup latency (0-100)
        resolution_score: Score for resolution (0-100)
        fps_score: Score for FPS (0-100)
        is_available: Whether channel is available
        latency_ms: Measured latency in ms
        resolution: Resolution string
        fps: FPS value
    """

    total_score: float
    availability_score: float = 0.0
    latency_score: float = 0.0
    resolution_score: float = 0.0
    fps_score: float = 0.0
    is_available: bool = False
    latency_ms: float = -1.0
    resolution: str = "Unknown"
    fps: float = -1.0

    def to_dict(self) -> dict:
        """Convert score to dictionary for export."""
        return {
            "total_score": self.total_score,
            "availability_score": self.availability_score,
            "latency_score": self.latency_score,
            "resolution_score": self.resolution_score,
            "fps_score": self.fps_score,
            "is_available": self.is_available,
            "latency_ms": self.latency_ms,
            "resolution": self.resolution,
            "fps": self.fps,
        }


class QualityScoreEngine:
    """
    Engine for calculating quality scores and ranking channels.
    """

    def __init__(self, profile: Optional[ScoreProfile] = None):
        """
        Initialize the quality score engine.

        Args:
            profile: Score profile configuration. Uses default if not provided.
        """
        self.profile = profile or ScoreProfile()

    def _parse_resolution(self, resolution: str) -> int:
        """Parse resolution string to tier level."""
        if resolution == "Unknown" or not resolution:
            return 0

        match = re.match(r"(\d+)x(\d+)", resolution)
        if not match:
            return 0

        width, height = int(match.group(1)), int(match.group(2))
        key = f"{width}x{height}"

        return RESOLUTION_PATTERNS.get(key, 0)

    def _calculate_availability_score(self, speed: float) -> float:
        """Calculate availability score based on speed."""
        if speed > 0:
            return 100.0
        return 0.0

    def _calculate_latency_score(self, latency_ms: float) -> float:
        """Calculate latency score with penalty."""
        if latency_ms < 0:
            return 0.0

        max_latency = self.profile.max_latency_ms
        if latency_ms >= max_latency:
            return 0.0

        penalty = latency_ms * self.profile.latency_penalty_per_ms
        score = 100.0 - penalty
        return max(0.0, score)

    def _calculate_resolution_score(self, resolution: str) -> float:
        """Calculate resolution score based on tier."""
        tier = self._parse_resolution(resolution)
        if tier == 0:
            return 0.0
        return min(100.0, tier * 12.5)

    def _calculate_fps_score(self, fps: float) -> float:
        """Calculate FPS score."""
        if fps < 0:
            return 0.0

        if fps >= 60:
            return 100.0
        if fps >= 50:
            return 85.0
        if fps >= 30:
            return 60.0
        if fps >= 24:
            return 40.0
        return 20.0

    def calculate_score(
        self,
        channel,
        latency_ms: Optional[float] = None,
    ) -> QualityScore:
        """
        Calculate quality score for a channel.

        Args:
            channel: Channel object with speed, resolution, fps attributes
            latency_ms: Optional latency in milliseconds. If not provided,
                       uses channel.startup_latency if available, else -1

        Returns:
            QualityScore object with breakdown
        """
        speed = getattr(channel, "speed", -1)
        resolution = getattr(channel, "resolution", "Unknown")
        fps = getattr(channel, "fps", -1.0)

        if latency_ms is None:
            latency_ms = getattr(channel, "startup_latency", -1.0)

        is_available = speed > 0

        availability_score = self._calculate_availability_score(speed)
        latency_score = self._calculate_latency_score(latency_ms)
        resolution_score = self._calculate_resolution_score(resolution)
        fps_score = self._calculate_fps_score(fps)

        total_score = (
            availability_score * self.profile.availability_weight / 100
            + latency_score * self.profile.latency_weight / 100
            + resolution_score * self.profile.resolution_weight / 100
            + fps_score * self.profile.fps_weight / 100
        )

        return QualityScore(
            total_score=round(total_score, 2),
            availability_score=round(availability_score, 2),
            latency_score=round(latency_score, 2),
            resolution_score=round(resolution_score, 2),
            fps_score=round(fps_score, 2),
            is_available=is_available,
            latency_ms=latency_ms,
            resolution=resolution,
            fps=fps,
        )

    def rank_channels(self, channels: list) -> list:
        """
        Rank channels by quality score (stable, reproducible order).

        Args:
            channels: List of Channel objects

        Returns:
            List of channels sorted by quality score (descending),
            stable for equal scores (by resolution, then name)
        """
        scored = []
        for ch in channels:
            score = self.calculate_score(ch)
            scored.append((ch, score))

        scored.sort(key=lambda x: -x[1].total_score)
        return scored
