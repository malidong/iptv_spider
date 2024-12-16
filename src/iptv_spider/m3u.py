# -*- coding: utf-8 -*-
# pylint: disable=line-too-long,broad-exception-caught
"""
M3U8 class to manage downloaded m3u8 contents,
with function to get a best channel in channels with the same name.
"""

import os
import re
import sys
import requests

from iptv_spider.channel import Channel

# 伪装为 PotPlayer 的 User-Agent
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/90.0.4430.212 Safari/537.36"}


class M3U8:
    """
    M3U8 class to manage downloaded m3u8 contents.
    black_servers list will store the server with speed 0.
    Speed test will skip when the server in black_servers list.
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
        Download file from internet
        :param url: http url of m3u8 file
        :param save_path: local path to save m3u8 file
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
            print(f"M3U 文件已保存到: {save_path}")
            return save_path
        except requests.exceptions.RequestException as e:
            print(f"错误: 无法下载 M3U 文件 - {str(e)}")
            sys.exit(-1)
        except Exception as e:
            print(f"错误: 下载 M3U 文件时发生异常 - {str(e)}")
            sys.exit(-1)

    def load_file(self, file_path: str, regex_filter: str = None) -> dict:
        """
        :param file_path: path of m3u8 to load
        :param regex_filter: regex filter for channel name, only load matched channels.
        :return:
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
                    # 提取meta信息
                    meta = line.split(",")[0].strip()
                    # 提取频道名称
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
        print(f"匹配到{str(len(filtered_channels))}个频道： {filtered_channels.keys()}")
        return filtered_channels

    def get_best_channels(self, speed_limit: int = 2) -> dict:
        """
        获得每个频道名的最大速度频道，如果已经有超出limit的频道则直接采用。
        :param speed_limit:
        :return:
        """
        best_channels: dict[str, Channel] = {}
        for channel_name, channels in self.channels.items():
            for c in channels:
                if c.media_url.split('/')[2] in self.black_servers:
                    print(f"Skip black server: {c.media_url.split('/')[2]}")
                    continue

                speed = c.get_speed()

                if speed == 0.0:
                    self.black_servers.append(c.media_url.split('/')[2])

                if channel_name not in best_channels:
                    best_channels[channel_name] = c
                elif speed > best_channels[channel_name].speed:
                    best_channels[channel_name] = c

                if speed > speed_limit * 1024 * 1024:
                    print(
                        f"{channel_name} Found channel with speed {str(speed)}, skip other channels with the same name.")
                    break

            if best_channels[channel_name].speed == 0:
                best_channels.pop(channel_name, None)

        return best_channels
