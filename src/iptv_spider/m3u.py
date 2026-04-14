# -*- coding: utf-8 -*-
# pylint: disable=line-too-long,broad-exception-caught
"""
M3U8 class to manage and process M3U8 playlist files.
This includes downloading M3U8 files, filtering channels by regex, and selecting the best channel based on download speed.
"""

import os
import re
import sys
import json
import time
import requests
from requests import Response
from pathlib import Path
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from iptv_spider.channel import Channel
from iptv_spider.logger import logger
from iptv_spider.utils import get_config_dir, url_fingerprint, utc_now_iso
from datetime import datetime, timezone, timedelta

# Simulating PotPlayer's User-Agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/90.0.4430.212 Safari/537.36"
}


class M3U8:
    """
    A class to manage M3U8 playlist files and associated channels.

    Attributes:
        url (str): URL or path to the M3U8 file.
        regex_filter (str): Regex pattern to filter channel names.
        channels (dict): A dictionary containing channel objects grouped by name.
        black_servers (list): A list of servers to avoid during speed tests due to poor performance.
        tested_servers (dict): A dict to cache the speed of servers, and test speed of channels from the best servers.
        max_retries (int): Maximum retry attempts for network requests.
        request_timeout (int): Timeout in seconds for HTTP requests.
    """

    __slots__ = (
        "url",
        "regex_filter",
        "channels",
        "black_servers",
        "tested_servers",
        "tested_channels",
        "max_retries",
        "request_timeout",
        "probe_timeout",
        "dedup_mode",
        "dedup_keep",
        "cache_enabled",
        "cache_ttl_hours",
        "cache_file",
        "cache_clear",
        "dedup_trace",
    )

    def __init__(
        self,
        path: str,
        regex_filter: str,
        max_retries: int = 3,
        request_timeout: int = 30,
        probe_timeout: int = 10,
        dedup_mode: str = "url_fingerprint",
        dedup_keep: str = "first",
        cache_enabled: bool = True,
        cache_ttl_hours: int = 24,
        cache_file: Optional[str] = None,
        cache_clear: bool = False,
    ):
        """
        Initialize an M3U8 object by loading channels from a file or URL.

        Args:
            path (str): Path or URL of the M3U8 file.
            regex_filter (str): Regex pattern to filter channel names.
            max_retries (int): Maximum retry attempts for network requests.
            request_timeout (int): Timeout in seconds for HTTP requests.
        """
        self.max_retries: int = max_retries
        self.request_timeout: int = request_timeout
        self.probe_timeout: int = probe_timeout

        if path.startswith("http"):
            path: str = self.download_m3u8_file(
                url=path, save_path=get_config_dir() / path.split("/")[-1]
            )
        self.regex_filter: str = regex_filter
        self.channels: dict[str, list[Channel]] = self.load_file(file_path=path)
        self.black_servers: list[str] = self.__load_black_servers()
        self.tested_servers: dict[str, float] = self.__load_tested_servers()
        self.tested_channels: dict[str, dict] = self.__load_tested_channels(
            path=Path(cache_file) if cache_file else None
        )
        self.dedup_mode: str = dedup_mode
        self.dedup_keep: str = dedup_keep
        self.cache_enabled: bool = cache_enabled
        self.cache_ttl_hours: int = cache_ttl_hours
        self.cache_file: Optional[str] = cache_file
        self.cache_clear: bool = cache_clear
        self.dedup_trace: list[dict] = []

        if self.cache_clear:
            self.tested_channels = {}
            self.__save_tested_channels(
                path=Path(self.cache_file) if self.cache_file else None
            )

        if self.dedup_mode == "url_fingerprint":
            self.__dedup_channels_by_fingerprint()

    def __load_black_servers(self, path: Optional[Path] = None) -> List[str]:
        """
        Load previously blacklisted server data from a JSON file.

        Args:
            path (Path): The path to find "black_servers.json" file.

        Returns:
            list: List of blacklisted server addresses.
        """
        black_servers_path = path if path else get_config_dir()
        black_servers_file = black_servers_path / "black_servers.json"
        try:
            if black_servers_file.is_file():
                with open(black_servers_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load black servers list: {e}")
        return []

    def __save_black_servers(self, path: Optional[Path] = None) -> None:
        """
        Save blacklisted server data to "black_servers.json".

        Args:
            path (Path): The folder path to save "black_servers.json" file.
        """
        black_servers_path = path if path else get_config_dir()
        black_servers_file = black_servers_path / "black_servers.json"
        try:
            with open(black_servers_file, "w", encoding="utf-8") as f:
                json.dump(self.black_servers, f, indent=4)
            logger.debug(f"Black servers list saved: {len(self.black_servers)} servers")
        except Exception as e:
            logger.warning(f"Failed to save black servers list: {e}")

    def __load_tested_servers(self, path: Optional[Path] = None) -> Dict[str, float]:
        """
        Load previously tested server data from a JSON file.

        Args:
            path (Path): The path to find "tested_servers.json" file.

        Returns:
            dict: Dictionary mapping server addresses to their tested speeds.
        """
        tested_servers_path = path if path else get_config_dir()
        tested_servers_file = tested_servers_path / "tested_servers.json"
        try:
            if tested_servers_file.is_file():
                with open(tested_servers_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load tested servers cache: {e}")
        return {}

    def __save_tested_servers(self, path: Optional[Path] = None) -> None:
        """
        Save tested server data to "tested_servers.json".

        Args:
            path (Path): The folder path to save "tested_servers.json" file.
        """
        tested_servers_path = path if path else get_config_dir()
        tested_servers_file = tested_servers_path / "tested_servers.json"
        try:
            with open(tested_servers_file, "w", encoding="utf-8") as f:
                json.dump(self.tested_servers, f, indent=4)
            logger.debug(
                f"Tested servers cache saved: {len(self.tested_servers)} servers"
            )
        except Exception as e:
            logger.warning(f"Failed to save tested servers cache: {e}")

    def __load_tested_channels(self, path: Optional[Path] = None) -> Dict[str, dict]:
        """
        Load previously tested channel data from a JSON file.

        Args:
            path (Path): Path to "tested_channels.json".

        Returns:
            dict: Dictionary mapping URL fingerprints to test metadata.
        """
        tested_channels_path = (
            path if path else get_config_dir() / "tested_channels.json"
        )
        try:
            if tested_channels_path.is_file():
                with open(tested_channels_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load tested channels cache: {e}")
        return {}

    def __save_tested_channels(self, path: Optional[Path] = None) -> None:
        """
        Save tested channel data to "tested_channels.json".

        Args:
            path (Path): The file path to save the cache.
        """
        tested_channels_path = (
            path if path else get_config_dir() / "tested_channels.json"
        )
        try:
            tested_channels_path.parent.mkdir(parents=True, exist_ok=True)
            with open(tested_channels_path, "w", encoding="utf-8") as f:
                json.dump(self.tested_channels, f, indent=4)
            logger.debug(
                f"Tested channels cache saved: {len(self.tested_channels)} entries"
            )
        except Exception as e:
            logger.warning(f"Failed to save tested channels cache: {e}")

    def __parse_cache_time(self, value: str) -> Optional[datetime]:
        """
        Parse ISO cache time to timezone-aware datetime (UTC).
        """
        try:
            if value.endswith("Z"):
                value = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            return None

    def __purge_expired_cache(self, now: datetime) -> None:
        """
        Remove expired cache entries based on TTL.
        """
        if not self.cache_enabled:
            return
        ttl = timedelta(hours=self.cache_ttl_hours)
        expired = []
        for fp, data in self.tested_channels.items():
            last_tested = data.get("last_tested")
            if not last_tested:
                continue
            parsed = self.__parse_cache_time(last_tested)
            if not parsed:
                continue
            if now - parsed > ttl:
                expired.append(fp)
        for fp in expired:
            self.tested_channels.pop(fp, None)

    def __dedup_channels_by_fingerprint(self) -> None:
        """
        Deduplicate channels by URL fingerprint within each channel name.
        """
        deduped: dict[str, list[Channel]] = {}
        for channel_name, channels in self.channels.items():
            seen: dict[str, Channel] = {}
            best_speed: dict[str, float] = {}
            for channel in channels:
                fp = url_fingerprint(channel.media_url)
                if fp not in seen:
                    seen[fp] = channel
                    cached_speed = self.tested_channels.get(fp, {}).get("speed")
                    if cached_speed is not None:
                        best_speed[fp] = float(cached_speed)
                    continue

                reason = "duplicate_url"
                if self.dedup_keep == "fastest":
                    cached_speed = self.tested_channels.get(fp, {}).get("speed")
                    if cached_speed is None:
                        self.dedup_trace.append(
                            {
                                "channel_name": channel.channel_name,
                                "media_url": channel.media_url,
                                "fingerprint": fp,
                                "action": "skip",
                                "reason": "no_cached_speed",
                            }
                        )
                        continue
                    cached_speed = float(cached_speed)
                    if fp not in best_speed or cached_speed > best_speed[fp]:
                        best_speed[fp] = cached_speed
                        seen[fp] = channel
                        reason = "keep_faster"
                    else:
                        reason = "skip_slower"
                else:
                    reason = "skip_first_kept"

                self.dedup_trace.append(
                    {
                        "channel_name": channel.channel_name,
                        "media_url": channel.media_url,
                        "fingerprint": fp,
                        "action": "deduplicated",
                        "reason": reason,
                    }
                )
            deduped[channel_name] = list(seen.values())
        self.channels = deduped

    def download_m3u8_file(self, url: str, save_path: Optional[Path] = None) -> str:
        """
        Download an M3U8 playlist file from the given URL with retry mechanism.

        Args:
            url (str): HTTP URL of the M3U8 file.
            save_path (Path, optional): Local path to save the downloaded file. Defaults to current directory.

        Returns:
            str: Local file path of the downloaded M3U8 file.
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"Downloading M3U8 file (attempt {attempt + 1}/{self.max_retries}): {url}"
                )
                response: Response = requests.get(
                    url, headers=HEADERS, timeout=self.request_timeout
                )
                response.raise_for_status()

                cwd: str = os.getcwd()
                if not save_path:
                    save_path: str = f"{cwd}/{url.split('/')[-1]}"

                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
                logger.info(f"M3U file saved to: {save_path}")
                return str(save_path)
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Error downloading M3U file (attempt {attempt + 1}): {str(e)}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(1)
            except Exception as e:
                logger.warning(
                    f"Exception while downloading M3U file (attempt {attempt + 1}): {str(e)}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(1)

        logger.error(
            f"Failed to download M3U file after {self.max_retries} attempts: {url}"
        )
        sys.exit(-1)

    def load_file(
        self, file_path: str, regex_filter: Optional[str] = None
    ) -> Dict[str, List[Channel]]:
        """
        Load and parse an M3U8 playlist file into channels.

        Args:
            file_path (str): Path to the M3U8 file.
            regex_filter (str, optional): Regex filter for channel names. Defaults to the instance's regex_filter.

        Returns:
            dict: A dictionary mapping channel names to lists of Channel objects.
        """
        if not regex_filter:
            regex_filter: str = self.regex_filter
        filtered_channels: dict = {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                while True:
                    line: str = f.readline()
                    if not line:
                        break

                    if line.startswith("#EXTINF"):
                        # Extract meta information and channel name
                        meta: str = line.split(",")[0].strip()
                        current_name: str = line.split(",")[-1].strip()
                        if not re.match(regex_filter, current_name):
                            continue

                        # Extract media URL
                        media_url: str = f.readline().strip()

                        if "udp" in media_url or "rtp" in media_url:
                            logger.debug(
                                f"UDP or RTP contents will cause stuck of the process. "
                                f"Skip this channel. {current_name}: {media_url}."
                            )
                            continue

                        channel: Channel = Channel(
                            meta=meta,
                            channel_name=current_name,
                            media_url=media_url,
                            max_retries=self.max_retries,
                            request_timeout=self.request_timeout,
                            probe_timeout=self.probe_timeout,
                        )

                        # Add the channel to the dictionary
                        if current_name not in filtered_channels:
                            filtered_channels[current_name] = [channel]
                        else:
                            filtered_channels[current_name].append(channel)

            logger.info(
                f"Matched {len(filtered_channels)} channels: {list(filtered_channels.keys())}"
            )
            return filtered_channels
        except FileNotFoundError:
            logger.error(f"M3U file not found: {file_path}")
            sys.exit(-1)
        except Exception as e:
            logger.error(f"Error loading M3U file: {str(e)}")
            sys.exit(-1)

    def __test_channel_speed(
        self, channel_name: str, channel: Channel, speed_limit_mb: int
    ) -> tuple:
        """
        Test a single channel's speed and return results.

        Args:
            channel_name (str): Name of the channel.
            channel (Channel): Channel object to test.
            speed_limit_mb (int): Speed limit in MB/s for early termination.

        Returns:
            tuple: (channel_name, channel, exceeds_limit) indicating if limit was exceeded.
        """
        try:
            speed = channel.get_speed()
            exceeds_limit = speed > speed_limit_mb * 1024 * 1024
            return channel_name, channel, exceeds_limit
        except Exception as e:
            logger.error(f"Error testing channel {channel_name}: {e}")
            return channel_name, channel, False

    def get_best_channels(self, speed_limit: int = 2, max_workers: int = 4) -> dict:
        """
        Select the best channel (fastest download speed) for each unique channel name using parallel testing.

        Args:
            speed_limit (int): Speed threshold (in MB/s). Channels exceeding this speed are immediately selected.
            max_workers (int): Number of concurrent threads for testing channels.

        Returns:
            dict: A dictionary mapping channel names to their best Channel object.
        """
        best_channels: dict[str, Channel] = {}
        channels_to_test: list = []
        now = datetime.now(timezone.utc)
        self.__purge_expired_cache(now)

        # Prepare channels for testing
        for channel_name, channels in self.channels.items():
            # Sort channels by previously tested server speeds (if available)
            channels.sort(
                key=lambda ch: self.tested_servers.get(ch.media_url.split("/")[2], 0),
                reverse=True,
            )

            for channel in channels:
                # Skip blacklisted servers
                server: str = channel.media_url.split("/")[2]
                if server in self.black_servers:
                    logger.debug(
                        f"Skipping blacklisted server: {server} for channel {channel_name}"
                    )
                    continue

                fingerprint = url_fingerprint(channel.media_url)
                if self.cache_enabled and fingerprint in self.tested_channels:
                    cached = self.tested_channels.get(fingerprint, {})
                    last_tested = cached.get("last_tested")
                    if last_tested:
                        cached_time = self.__parse_cache_time(last_tested)
                        if cached_time and now - cached_time <= timedelta(
                            hours=self.cache_ttl_hours
                        ):
                            channel.speed = cached.get("speed", channel.speed)
                            channel.resolution = cached.get(
                                "resolution", channel.resolution
                            )
                            channel.fps = float(cached.get("fps", channel.fps))
                            if channel_name not in best_channels:
                                best_channels[channel_name] = channel
                            elif channel.speed > best_channels[channel_name].speed:
                                best_channels[channel_name] = channel
                            if (
                                server not in self.tested_servers
                                or channel.speed > self.tested_servers[server]
                            ):
                                self.tested_servers[server] = channel.speed
                            continue

                channels_to_test.append((channel_name, channel))

        # Test channels in parallel
        logger.info(
            f"Starting parallel speed tests for {len(channels_to_test)} channels with {max_workers} workers..."
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.__test_channel_speed, ch_name, ch, speed_limit): (
                    ch_name,
                    ch,
                )
                for ch_name, ch in channels_to_test
            }

            for future in as_completed(futures):
                channel_name, channel = futures[future]
                try:
                    result_ch_name, result_channel, exceeds_limit = future.result()
                    server: str = result_channel.media_url.split("/")[2]
                    speed: float = result_channel.speed

                    # Blacklist servers with zero speed
                    if speed == 0.0:
                        self.black_servers.append(server)
                        logger.debug(f"Blacklisted server {server} (zero speed)")
                        continue

                    # Update the best channel for this name
                    if result_ch_name not in best_channels:
                        best_channels[result_ch_name] = result_channel
                    elif speed > best_channels[result_ch_name].speed:
                        best_channels[result_ch_name] = result_channel

                    # Update tested server speed
                    if (
                        server not in self.tested_servers
                        or speed > self.tested_servers[server]
                    ):
                        self.tested_servers[server] = speed
                    # Update tested channel cache
                    fingerprint = url_fingerprint(result_channel.media_url)
                    self.tested_channels[fingerprint] = {
                        "speed": speed,
                        "resolution": result_channel.resolution,
                        "fps": result_channel.fps,
                        "last_tested": utc_now_iso(),
                        "media_url": result_channel.media_url,
                        "channel_name": result_channel.channel_name,
                    }

                except Exception as e:
                    logger.error(
                        f"Error processing test result for {channel_name}: {e}"
                    )

        # Remove channels with no valid speed
        invalid_channels = [
            ch_name
            for ch_name in best_channels
            if best_channels[ch_name].speed == 0 or best_channels[ch_name].speed < 0
        ]
        for ch_name in invalid_channels:
            best_channels.pop(ch_name, None)

        # Save updated caches
        self.__save_black_servers()
        self.__save_tested_servers()
        if self.cache_enabled:
            self.__save_tested_channels(
                path=Path(self.cache_file) if self.cache_file else None
            )

        logger.info(
            f"Testing completed. Best channels: {len(best_channels)}, Blacklisted servers: {len(self.black_servers)}"
        )
        return best_channels
