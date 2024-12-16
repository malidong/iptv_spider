# -*- coding: utf-8 -*-
# pylint: disable=line-too-long,broad-exception-caught
"""
M3U8 class to manage downloaded m3u8 contents,
with function to get the best channel among channels with the same name.
"""

import os
import re
import sys
import requests

from iptv_spider.channel import Channel
from iptv_spider.logger import logger

# Simulating PotPlayer's User-Agent
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/90.0.4430.212 Safari/537.36"}


class M3U8:
    """
    M3U8 class to manage downloaded m3u8 contents.
    The `black_servers` list stores servers with a speed of 0.
    Speed tests will skip servers in the `black_servers` list.
    """
    __slots__ = ("url",
                 "regex_filter",
                 "channels",
                 "black_servers")

    def __init__(self, path: str, regex_filter: str):
        if path.startswith("http"):
            path = self.download_m3u8_file(url=path)
        self.regex_filter: str = regex_filter
        self.channels: dict[str, list[Channel]] = self.load_file(file_path=path)
        self.black_servers: list[str] = []

    def download_m3u8_file(self, url: str, save_path: str = None) -> str:
        """
        Download file from the internet.
        :param url: HTTP URL of the m3u8 file
        :param save_path: Local path to save the m3u8 file
        :return:
        """
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            cwd = os.getcwd()
            if not save_path:
                save_path = f"{cwd}/{url.split('/')[-1]}"
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
        Load channels from the m3u8 file.
        :param file_path: Path of the m3u8 file to load
        :param regex_filter: Regex filter for channel names; only load matching channels.
        :return: A dictionary of filtered channels
        """
        if not regex_filter:
            regex_filter = self.regex_filter
        filtered_channels = {}

        with open(file_path, 'r', encoding='utf-8') as f:
            while True:
                line = f.readline()
                if not line:
                    break

                if line.startswith("#EXTINF"):
                    # Extract meta information
                    meta = line.split(",")[0].strip()
                    # Extract channel name
                    current_name = line.split(",")[-1].strip()
                    if not re.match(regex_filter, current_name):
                        continue

                    media_url = f.readline().strip()
                    c = Channel(meta=meta,
                                channel_name=current_name,
                                media_url=media_url)
                    if current_name not in filtered_channels:
                        filtered_channels[current_name] = [c]
                    else:
                        filtered_channels[current_name].append(c)
        logger.info(f"Matched {str(len(filtered_channels))} channels: {filtered_channels.keys()}")
        return filtered_channels

    def get_best_channels(self, speed_limit: int = 2) -> dict:
        """
        Get the fastest channel for each channel name.
        If a channel exceeds the speed limit, it will be chosen directly.
        :param speed_limit: Speed limit for selecting channels (in MB/s).
        :return: A dictionary of the best channels.
        """
        best_channels: dict[str, Channel] = {}
        for channel_name, channels in self.channels.items():
            for c in channels:
                if c.media_url.split('/')[2] in self.black_servers:
                    logger.info(f"Skip black server: {c.media_url.split('/')[2]}")
                    continue

                speed = c.get_speed()

                if speed == 0.0:
                    self.black_servers.append(c.media_url.split('/')[2])

                if channel_name not in best_channels:
                    best_channels[channel_name] = c
                elif speed > best_channels[channel_name].speed:
                    best_channels[channel_name] = c

                if speed > speed_limit * 1024 * 1024:
                    logger.info(
                        f"{channel_name} Found channel with speed {str(speed)}, "
                        f"skip other channels with the same name.")
                    break

            if best_channels[channel_name].speed == 0:
                best_channels.pop(channel_name, None)

        return best_channels
