# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
# pylint: disable=broad-exception-caught
"""
Channel class with functions to test speed and get resolution.
Sample:
#EXTINF:-1  tvg-name="CCTV2" tvg-logo="https://live.fanmingming.com/tv/CCTV2.png"  group-title="🌐 Central Channels",CCTV2
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
                  "Chrome/90.0.4430.212 Safari/537.36"}


class Channel:
    """
    Channel class with two-line structure:
    → metadata, channel_name
    → media_url
    If the media_url ends with m3u or m3u8,
    this channel is not a direct channel and has a nested m3u8 structure.
    """
    __slots__ = ("meta",
                 "channel_name",
                 "media_url",
                 "is_direct",
                 "speed",
                 "resolution")

    def __init__(self, meta: str, channel_name: str, media_url: str):
        """

        :param meta: Metadata before the channel name in #EXTINF:
        :param channel_name: Channel name in #EXTINF:
        :param media_url: Media URL
        """
        self.meta = meta
        self.channel_name = channel_name
        self.media_url = media_url
        # If the URL does not end with m3u8 or m3u, it is a direct play channel.
        # However, in some cases, it redirects to download m3u8 or m3u files,
        # which cannot be handled at the moment.
        self.is_direct = media_url.endswith("m3u") or media_url.endswith("m3u8")
        self.speed = None
        self.resolution = None

    def get_speed(self) -> float:
        """
        Get the playback speed of this channel.
        :return: Speed of this channel
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
        Get the resolution of the ts_url.
        :param ts_url: If ts_url is None, will use self.media_url
        :return: Resolution as a string
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
            result = subprocess.run(command,
                                    capture_output=True,
                                    text=True,
                                    timeout=10,
                                    check=False)
            if result.returncode == 0:
                resolution = result.stdout.strip()
                return resolution if resolution else None

            return "Failed to get resolution"
        except subprocess.TimeoutExpired:
            logger.warning(f"Error: Timed out while getting video resolution - {ts_url}")
        except Exception as e:
            logger.warning(f"Error: An exception occurred while getting video resolution - {str(e)}")
        return "Unknown resolution"

    def __test_m3u8_bandwidth(self, max_ts: int = 5, max_workers: int = 2) -> float:
        """
        Download and test the bandwidth of each TS file in the M3U8 playlist.
        For multiple TS files, get the maximum download speed.
        :param max_ts: Max number of TS files to test
        :param max_workers: Maximum number of processes
        :return: Maximum download speed
        """
        try:
            # Download and parse the M3U8 file
            m3u8_content = requests.get(self.media_url, headers=HEADERS, timeout=10).text
            playlist = m3u8.loads(m3u8_content)

            # Get TS file URLs
            ts_urls = [segment.uri for segment in playlist.segments]
            if not ts_urls:
                return 0

            # Test only the first max_ts TS files
            ts_urls = ts_urls[:max_ts]

            # Download and test the bandwidth of each TS file
            results = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self.__test_download_speed, ts_url) for ts_url in ts_urls]
                for future in as_completed(futures):
                    try:
                        results.append(future.result())
                    except Exception as e:
                        logger.warning(f"Unknown error when completing multithread of "
                                       f"Channel.__test_download_speed: {e}")
                        return 0.0
            self.resolution = self.get_video_resolution(ts_url=ts_urls[0])
            return max(results)
        except requests.exceptions.RequestException as e:
            logger.warning(f"RequestException during M3U8 speed test: {e}")
            return 0.0
        except Exception as e:
            logger.warning(f"Unknown error during M3U8 speed test: {e}")
            return 0.0

    def __test_download_speed(self, ts_url: str, m3u8_base_url: str = None) -> float:
        """
        Download and test the bandwidth of a TS file. Some M3U8 playlists use relative paths,
        requiring combination with the M3U8 base URL.
        :param ts_url: URL of the TS file in the M3U8 playlist
        :param m3u8_base_url: Base URL of the M3U8 playlist
        :return: Download speed
        """
        if not m3u8_base_url:
            m3u8_base_url = self.media_url
        # If the TS file is a relative path, combine it with the M3U8 base URL
        if not ts_url.startswith('http'):
            ts_url = urljoin(m3u8_base_url, ts_url)  # Use urljoin to combine relative path with base URL
        try:
            logger.info(f"Testing download: {ts_url}")
            start_time = time.time()
            response = requests.get(ts_url,
                                    headers=HEADERS,
                                    stream=True,
                                    timeout=20)  # Set timeout to 20 seconds
            response.raise_for_status()

            total_size = 0  # Downloaded data size (in bytes)
            for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
                total_size += len(chunk)
                if total_size >= 5 * 1024 * 1024:  # Limit to 5MB of data
                    break
                # Check if it exceeds 20 seconds
                if time.time() - start_time > 20:
                    raise TimeoutError("Download timed out: Exceeded 20 seconds")

            elapsed_time = time.time() - start_time
            speed = total_size / elapsed_time  # Download speed = Data size / Time
            return speed
        except TimeoutError as te:
            logger.warning(f"TimeoutError during TS download test: {te}")
            return 0.0
        except requests.exceptions.RequestException as e:
            logger.warning(f"RequestException during TS download test: {e}")
            return 0.0
        except Exception as e:
            logger.warning(f"Unknown error during TS download test: {e}")
            return 0.0

    def __test_direct_bandwidth(self) -> float:
        """
        If the URL is not an M3U8 file but a direct play URL,
        the bandwidth can be tested directly.
        :return: Download speed
        """
        try:
            start_time = time.time()
            response = requests.get(self.media_url,
                                    headers=HEADERS,
                                    stream=True,
                                    timeout=20)  # Set timeout to 20 seconds
            response.raise_for_status()

            total_size = 0  # Downloaded data size (in bytes)
            for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
                total_size += len(chunk)
                if total_size >= 5 * 1024 * 1024:  # Limit to 5MB of data
                    break
                # Check if it exceeds 20 seconds
                if time.time() - start_time > 20:
                    raise TimeoutError("Download timed out: Exceeded 20 seconds")

            elapsed_time = time.time() - start_time
            speed = total_size / elapsed_time  # Download speed = Data size / Time
            self.resolution = self.get_video_resolution(ts_url=self.media_url)
            return speed
        except TimeoutError:
            return 0.0
        except requests.exceptions.RequestException:
            return 0.0
        except Exception:
            return 0.0
