# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
# pylint: disable=broad-exception-caught
"""
Channel module for testing IPTV stream quality.

This module defines a `Channel` class to represent and evaluate IPTV streams.
Features include:
- Download speed testing for direct and M3U8-based streams.
- Resolution extraction from TS or media URLs.

Typical usage:
#EXTINF:-1 tvg-name="CCTV2" tvg-logo="https://live.fanmingming.com/tv/CCTV2.png" group-title="🌐 Central Channels",CCTV2
http://39.165.196.149:9003//hls/2/index.m3u8
"""

from math import floor, ceil
from urllib.parse import urljoin
import subprocess
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    """
    __slots__ = ("meta", "channel_name", "media_url", "is_direct", "speed", "resolution")

    def __init__(self, meta: str, channel_name: str, media_url: str):
        """
        Initializes a Channel object.

        Args:
            meta (str): Metadata for the channel (e.g., from the #EXTINF tag).
            channel_name (str): Name of the channel.
            media_url (str): Media stream URL.
        """
        self.meta: str = meta
        self.channel_name: str = channel_name
        self.media_url: str = media_url
        self.is_direct: bool = media_url.endswith("m3u") or media_url.endswith("m3u8")
        self.speed: float = -1
        self.resolution: str = "Unknown"

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
            cpu_threads = os.cpu_count()
            self.speed = self.__test_m3u8_bandwidth(max_ts=ceil(cpu_threads / 2),
                                                    max_workers=floor(cpu_threads / 2))
        logger.info(f"Channel speed test completed: {self.speed}")
        return self.speed

    def get_video_resolution(self, ts_url: str) -> str:
        """
        Extracts the video resolution of the given TS stream.

        Args:
            ts_url (str): URL of the TS segment or media.

        Returns:
            str: Video resolution (e.g., '1920x1080') or error message.
        """
        try:
            command = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=p=0",
                ts_url
            ]
            result: subprocess.CompletedProcess = subprocess.run(command,
                                                                 capture_output=True,
                                                                 text=True,
                                                                 timeout=10,
                                                                 check=False)
            if result.returncode == 0:
                resolution = result.stdout.strip()
                return resolution if resolution else None

            return "Failed to get resolution"
        except subprocess.TimeoutExpired:
            logger.warning(f"Timed out while getting video resolution - {ts_url}")
        except Exception as e:
            logger.warning(f"Exception while getting video resolution: {str(e)}")
        return "Unknown resolution"

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
            m3u8_content: str = requests.get(self.media_url, headers=HEADERS, timeout=10).text
            playlist = m3u8.loads(m3u8_content)

            ts_urls: list = [segment.uri for segment in playlist.segments]
            if not ts_urls:
                return 0

            ts_urls: list = ts_urls[:max_ts]

            results: list = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self.__test_download_speed, ts_url) for ts_url in ts_urls]
                for future in as_completed(futures):
                    try:
                        results.append(future.result())
                    except Exception as e:
                        logger.warning(f"Error testing TS download speed: {e}")
                        return 0.0
            self.resolution = self.get_video_resolution(ts_url=ts_urls[0])
            return max(results)
        except requests.exceptions.RequestException as e:
            logger.warning(f"RequestException during M3U8 speed test: {e}")
            return 0.0
        except Exception as e:
            logger.warning(f"Error during M3U8 speed test: {e}")
            return 0.0

    def __test_download_speed(self, ts_url: str, m3u8_base_url: str = None) -> float:
        """
        Tests the download speed of a single TS segment.

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
        try:
            logger.info(f"Testing download: {ts_url}")
            start_time: float = time.time()
            response: requests.Response = requests.get(ts_url, headers=HEADERS, stream=True, timeout=20)
            response.raise_for_status()

            total_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                total_size += len(chunk)
                if total_size >= 5 * 1024 * 1024:
                    break
                if time.time() - start_time > 20:
                    raise TimeoutError("Download timed out")

            elapsed_time: float = time.time() - start_time
            return total_size / elapsed_time
        except TimeoutError as te:
            logger.warning(f"Timeout during TS download: {te}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error during TS download: {e}")
        except Exception as e:
            logger.warning(f"Unknown error during TS download: {e}")

        return 0.0

    def __test_direct_bandwidth(self) -> float:
        """
        Tests the bandwidth of a direct media URL.

        Returns:
            float: Download speed in bytes per second.
        """
        try:
            start_time = time.time()
            response = requests.get(self.media_url, headers=HEADERS, stream=True, timeout=20)
            response.raise_for_status()

            total_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                total_size += len(chunk)
                if total_size >= 5 * 1024 * 1024:
                    break
                if time.time() - start_time > 20:
                    raise TimeoutError("Download timed out")

            elapsed_time = time.time() - start_time
            self.resolution = self.get_video_resolution(ts_url=self.media_url)
            return total_size / elapsed_time
        except TimeoutError as te:
            logger.warning(f"Timeout during TS download: {te}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error during TS download: {e}")
        except Exception as e:
            logger.warning(f"Unknown error during TS download: {e}")

        return 0.0
