# -*- coding: utf-8 -*-
# pylint: disable=line-too-long,broad-exception-caught
"""
M3U8 class to manage and process M3U8 playlist files.
This includes downloading M3U8 files, filtering channels by regex, and selecting the best channel based on download speed.
"""

import os
import re
import sys
import requests
from requests import Response

from iptv_spider.channel import Channel
from iptv_spider.logger import logger

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
    """
    __slots__ = ("url", "regex_filter", "channels", "black_servers")

    def __init__(self, path: str, regex_filter: str):
        """
        Initialize an M3U8 object by loading channels from a file or URL.

        Args:
            path (str): Path or URL of the M3U8 file.
            regex_filter (str): Regex pattern to filter channel names.
        """
        if path.startswith("http"):
            path: str = self.download_m3u8_file(url=path)
        self.regex_filter: str = regex_filter
        self.channels: dict[str, list[Channel]] = self.load_file(file_path=path)
        self.black_servers: list[str] = []

    def download_m3u8_file(self, url: str, save_path: str = None) -> str:
        """
        Download an M3U8 playlist file from the given URL.

        Args:
            url (str): HTTP URL of the M3U8 file.
            save_path (str, optional): Local path to save the downloaded file. Defaults to current directory.

        Returns:
            str: Local file path of the downloaded M3U8 file.
        """
        try:
            response: Response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            cwd: str = os.getcwd()
            if not save_path:
                save_path: str = f"{cwd}/{url.split('/')[-1]}"
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"M3U file saved to: {save_path}")
            return save_path
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: Unable to download M3U file - {str(e)}")
            sys.exit(-1)
        except Exception as e:
            logger.error(f"Error: Exception occurred while downloading M3U file - {str(e)}")
            sys.exit(-1)

    def load_file(self, file_path: str, regex_filter: str = None) -> dict:
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

        with open(file_path, 'r', encoding='utf-8') as f:
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

                    if "udp" in media_url:
                        logger.info(f"UDP contents will cause stuck of the process, now we cannot handle."
                                    f"Skip this channel. {current_name}: {media_url}.")
                        continue
                    channel: Channel = Channel(meta=meta, channel_name=current_name, media_url=media_url)

                    # Add the channel to the dictionary
                    if current_name not in filtered_channels:
                        filtered_channels[current_name] = [channel]
                    else:
                        filtered_channels[current_name].append(channel)

        logger.info(f"Matched {len(filtered_channels)} channels: {list(filtered_channels.keys())}")
        return filtered_channels

    def get_best_channels(self, speed_limit: int = 2) -> dict:
        """
        Select the best channel (fastest download speed) for each unique channel name.

        Args:
            speed_limit (int): Speed threshold (in MB/s). Channels exceeding this speed are immediately selected.

        Returns:
            dict: A dictionary mapping channel names to their best Channel object.
        """
        best_channels: dict[str, Channel] = {}
        for channel_name, channels in self.channels.items():
            for channel in channels:
                # Skip blacklisted servers
                server: str = channel.media_url.split('/')[2]
                if server in self.black_servers:
                    logger.info(f"Skipping blacklisted server: {server}")
                    continue

                # Test channel speed
                speed: float = channel.get_speed()

                # Blacklist servers with zero speed
                if speed == 0.0:
                    self.black_servers.append(server)

                # Update the best channel for this name
                if channel_name not in best_channels:
                    best_channels[channel_name] = channel
                elif speed > best_channels[channel_name].speed:
                    best_channels[channel_name] = channel

                # If speed exceeds the limit, select immediately
                if speed > speed_limit * 1024 * 1024:
                    logger.info(
                        f"{channel_name}: Found a channel with speed {speed}, "
                        f"skipping other channels with the same name."
                    )
                    break

            # Remove channels with no valid speed
            if best_channels.get(channel_name, None) and best_channels[channel_name].speed == 0:
                best_channels.pop(channel_name, None)

        return best_channels
