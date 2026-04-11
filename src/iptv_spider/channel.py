# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
# pylint: disable=broad-exception-caught
"""
Channel module for testing IPTV stream quality.

This module defines a `Channel` class to represent and evaluate IPTV streams.
Features include:
- Download speed testing for direct and M3U8-based streams.
- Resolution extraction from TS or media URLs.
- Retry mechanism for failed network requests.

Typical usage:
#EXTINF:-1 tvg-name="CCTV2" tvg-logo="https://live.fanmingming.com/tv/CCTV2.png" group-title="🌐 Central Channels",CCTV2
http://39.165.196.149:9003//hls/2/index.m3u8
"""

from math import floor, ceil
import json
from urllib.parse import urljoin
import subprocess
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Any
import requests
import m3u8

from iptv_spider.logger import logger

# Simulating PotPlayer's User-Agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/90.0.4430.212 Safari/537.36"
}


class Channel:
    """
    Represents an IPTV channel with metadata, stream URL, and utilities for testing stream quality.

    Attributes:
        meta (str): Metadata describing the channel (e.g., from the #EXTINF tag).
        channel_name (str): Name of the channel.
        media_url (str): URL of the media stream (can be M3U/M3U8 or direct TS).
        is_direct (bool): Whether the URL is a direct stream (ends with .m3u or .m3u8).
        speed (float): Measured download speed of the stream in bytes per second.
        resolution (str): Video resolution of the stream (e.g., '1920x1080').
        max_retries (int): Maximum number of retry attempts for network requests.
        request_timeout (int): Timeout in seconds for HTTP requests.
    """
    __slots__ = (
        "meta",
        "channel_name",
        "media_url",
        "is_direct",
        "speed",
        "resolution",
        "fps",
        "max_retries",
        "request_timeout",
        "probe_timeout",
        "_ffprobe_metadata",
    )

    def __init__(
        self,
        meta: str,
        channel_name: str,
        media_url: str,
        max_retries: int = 3,
        request_timeout: int = 30,
        probe_timeout: int = 10,
    ):
        """
        Initializes a Channel object.

        Args:
            meta (str): Metadata for the channel (e.g., from the #EXTINF tag).
            channel_name (str): Name of the channel.
            media_url (str): Media stream URL.
            max_retries (int): Maximum retry attempts for network requests.
            request_timeout (int): Timeout in seconds for HTTP requests.
        """
        self.meta: str = meta
        self.channel_name: str = channel_name
        self.media_url: str = media_url
        self.is_direct: bool = media_url.endswith("m3u") or media_url.endswith("m3u8")
        self.speed: float = -1
        self.resolution: str = "Unknown"
        self.fps: float = -1.0
        self.max_retries: int = max_retries
        self.request_timeout: int = request_timeout
        self.probe_timeout: int = probe_timeout
        self._ffprobe_metadata: dict[str, Any] = {}

    @staticmethod
    def _parse_ffprobe_rate(rate_value: Any) -> float:
        """
        Convert an ffprobe rate value into a float FPS estimate.
        """
        try:
            if rate_value in (None, "", "N/A"):
                return -1.0
            if isinstance(rate_value, (int, float)):
                return float(rate_value)
            if isinstance(rate_value, str):
                if "/" in rate_value:
                    numerator, denominator = rate_value.split("/", 1)
                    denominator_value = float(denominator)
                    if denominator_value == 0:
                        return -1.0
                    return float(numerator) / denominator_value
                return float(rate_value)
        except Exception:
            return -1.0
        return -1.0

    def get_ffprobe_metadata(self, ts_url: Optional[str] = None) -> dict[str, Any]:
        """
        Extract video metadata using ffprobe.

        Returns safe defaults when ffprobe is unavailable or the stream cannot be probed.
        Results are cached on the channel instance to avoid repeated subprocess calls.
        """
        if self._ffprobe_metadata:
            return self._ffprobe_metadata

        probe_url = ts_url or self.media_url
        metadata: dict[str, Any] = {
            "resolution": "Unknown",
            "fps": -1.0,
        }

        try:
            command = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,avg_frame_rate,r_frame_rate",
                "-of", "json",
                probe_url,
            ]
            result: subprocess.CompletedProcess = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.probe_timeout,
                check=False,
            )
            if result.returncode != 0:
                logger.warning(
                    f"ffprobe returned non-zero exit status for {self.channel_name}: {result.stderr.strip() if result.stderr else 'unknown error'}"
                )
            else:
                payload = json.loads(result.stdout or "{}")
                streams = payload.get("streams") or []
                stream = streams[0] if streams else {}
                width = stream.get("width")
                height = stream.get("height")
                if isinstance(width, int) and isinstance(height, int) and width > 0 and height > 0:
                    metadata["resolution"] = f"{width}x{height}"
                fps = self._parse_ffprobe_rate(stream.get("avg_frame_rate"))
                if fps < 0:
                    fps = self._parse_ffprobe_rate(stream.get("r_frame_rate"))
                if fps >= 0:
                    metadata["fps"] = fps
        except subprocess.TimeoutExpired:
            logger.warning(
                f"Timed out while probing metadata for {self.channel_name} - {probe_url}"
            )
        except FileNotFoundError:
            logger.warning("ffprobe executable was not found; video metadata will be unavailable")
        except json.JSONDecodeError:
            logger.warning(f"Invalid ffprobe output for {self.channel_name}: {probe_url}")
        except Exception as e:
            logger.warning(f"Exception while probing metadata for {self.channel_name}: {str(e)}")

        self._ffprobe_metadata = metadata
        self.resolution = metadata["resolution"]
        self.fps = metadata["fps"]
        return self._ffprobe_metadata

    def get_speed(self) -> float:
        """
        Tests the download speed of the channel stream.

        Returns:
            float: The download speed in bytes per second.
        """
        logger.info(f"{self.channel_name} Testing download speed: {self.media_url}")
        if self.is_direct:
            self.speed = self.__test_direct_bandwidth()
        else:
            cpu_threads = os.cpu_count() or 4
            self.speed = self.__test_m3u8_bandwidth(max_ts=ceil(cpu_threads / 2),
                                                    max_workers=floor(cpu_threads / 2))
        logger.info(f"Channel speed test completed: {self.speed / 1024:.2f} KB/s.")
        return self.speed

    def get_video_resolution(self, ts_url: str) -> str:
        """
        Extracts the video resolution of the given TS stream.

        Args:
            ts_url (str): URL of the TS segment or media.

        Returns:
            str: Video resolution (e.g., '1920x1080') or error message.
        """
        metadata = self.get_ffprobe_metadata(ts_url=ts_url)
        return metadata.get("resolution", "Unknown")

    def __test_m3u8_bandwidth(self, max_ts: int = 5, max_workers: int = 2) -> float:
        """
        Tests the download speed of M3U8 streams by analyzing TS segments.

        Args:
            max_ts (int): Maximum number of TS segments to test.
            max_workers (int): Number of concurrent threads for testing.

        Returns:
            float: Maximum download speed across tested TS segments.
        """
        try:
            response = requests.get(self.media_url, headers=HEADERS, timeout=self.request_timeout)
            response.raise_for_status()
            m3u8_content = response.text
            playlist = m3u8.loads(m3u8_content)

            ts_urls: list = [segment.uri for segment in playlist.segments]
            if not ts_urls:
                return 0.0

            ts_urls: list = ts_urls[:max_ts]

            results: list = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self.__test_download_speed, ts_url) for ts_url in ts_urls]
                for future in as_completed(futures):
                    try:
                        results.append(future.result())
                    except Exception as e:
                        logger.warning(f"Error testing TS download speed: {e}")
                        continue

            self.get_ffprobe_metadata(ts_url=ts_urls[0])
            return max(results) if results else 0.0
        except requests.exceptions.RequestException as e:
            logger.warning(f"RequestException during M3U8 speed test for {self.channel_name}: {e}")
            return 0.0
        except Exception as e:
            logger.warning(f"Error during M3U8 speed test for {self.channel_name}: {e}")
            return 0.0

    def __test_download_speed(self, ts_url: str, m3u8_base_url: Optional[str] = None) -> float:
        """
        Tests the download speed of a single TS segment with retry mechanism.

        Args:
            ts_url (str): URL of the TS segment.
            m3u8_base_url (str): Base URL for resolving relative paths.

        Returns:
            float: Download speed in bytes per second.
        """
        if not m3u8_base_url:
            m3u8_base_url: str = self.media_url
        if not ts_url.startswith('http'):
            ts_url: str = urljoin(m3u8_base_url, ts_url)

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Testing download (attempt {attempt + 1}/{self.max_retries}): {ts_url}")
                start_time: float = time.time()
                response: requests.Response = requests.get(
                    ts_url, headers=HEADERS, stream=True, timeout=self.request_timeout
                )
                response.raise_for_status()

                total_size = 0
                try:
                    for chunk in response.iter_content(chunk_size=8192):
                        total_size += len(chunk)
                        if total_size >= 5 * 1024 * 1024:
                            break
                        if time.time() - start_time > self.request_timeout:
                            raise TimeoutError(f"Download timed out after {self.request_timeout}s")
                finally:
                    response.close()

                elapsed_time: float = time.time() - start_time
                if elapsed_time > 0:
                    speed = total_size / elapsed_time
                    logger.info(f"Download speed: {speed / (1024 * 1024):.2f} MB/s")
                    return speed
                return 0.0
            except TimeoutError as te:
                logger.warning(f"Timeout during TS download (attempt {attempt + 1}): {te}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error during TS download (attempt {attempt + 1}): {e}")
            except Exception as e:
                logger.warning(f"Unknown error during TS download (attempt {attempt + 1}): {e}")

            # Wait before retrying
            if attempt < self.max_retries - 1:
                time.sleep(1)

        return 0.0

    def __test_direct_bandwidth(self) -> float:
        """
        Tests the bandwidth of a direct media URL with retry mechanism.

        Returns:
            float: Download speed in bytes per second.
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Testing direct bandwidth (attempt {attempt + 1}/{self.max_retries}): {self.media_url}")
                start_time = time.time()
                response = requests.get(
                    self.media_url, headers=HEADERS, stream=True, timeout=self.request_timeout
                )
                response.raise_for_status()

                total_size = 0
                try:
                    for chunk in response.iter_content(chunk_size=8192):
                        total_size += len(chunk)
                        if total_size >= 5 * 1024 * 1024:
                            break
                        if time.time() - start_time > self.request_timeout:
                            raise TimeoutError(f"Download timed out after {self.request_timeout}s")
                finally:
                    response.close()

                elapsed_time = time.time() - start_time
                self.get_ffprobe_metadata(ts_url=self.media_url)
                if elapsed_time > 0:
                    speed = total_size / elapsed_time
                    logger.info(f"Download speed: {speed / (1024 * 1024):.2f} MB/s")
                    return speed
                return 0.0
            except TimeoutError as te:
                logger.warning(f"Timeout during direct bandwidth test (attempt {attempt + 1}): {te}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error during direct bandwidth test (attempt {attempt + 1}): {e}")
            except Exception as e:
                logger.warning(f"Unknown error during direct bandwidth test (attempt {attempt + 1}): {e}")

            # Wait before retrying
            if attempt < self.max_retries - 1:
                time.sleep(1)

        return 0.0
