# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
# pylint: disable=broad-exception-caught
"""
# This is the entry module for iptv_spider.
"""
from argparse import Namespace
from datetime import datetime
import json
import argparse
from iptv_spider.m3u import M3U8
from iptv_spider.logger import logger


def arg_parser() -> Namespace:
    """
    Parse command-line arguments to get the download URL and filter pattern (optional).
    :return: Parsed arguments as a Namespace object.
    """
    parser = argparse.ArgumentParser(
        description="Parse download URL (url_or_path) and filter pattern (filter) from command-line arguments. "
                    "Both are optional.")

    # Add argument: url_or_path (optional, string type)
    parser.add_argument(
        "--url_or_path",
        type=str,
        default="https://live.iptv365.org/live.m3u",
        help="URL or file path, default is https://live.iptv365.org/live.m3u"
    )

    # Add argument: filter (optional, string type)
    parser.add_argument(
        "--filter",
        type=str,
        default=r'\b(cctv|CCTV)-?(?:[1-9]|1[0-7]|5\+?)\b',
        help="Regular expression for matching channels, default matches CCTV channels"
    )

    # Parse command-line arguments
    params = parser.parse_args()
    return params


# Main program
def main(m3u_url, regex_filter: str):
    """
    Read the IPTV list from a URL or local path, filter channel names using regex_filter,
    and retrieve the fastest URL for each channel with the same name.
    :param m3u_url: URL or local path of the m3u8 file to be downloaded.
    :param regex_filter: Regular expression for filtering channel names.
    :return:
    """
    # Download the M3U file
    m = M3U8(path=m3u_url, regex_filter=regex_filter)
    best = m.get_best_channels()

    best_channels = {}

    for channel_name, channel in best.items():
        best_channels[channel_name] = {
            "name": channel.channel_name,
            "media_url": channel.media_url,
            "speed": channel.speed,
            "resolution": channel.resolution,
        }

    # Save results to a JSON file
    with open(f"./best_cctv_{datetime.today().strftime('%Y-%m-%d')}.txt", 'w', encoding='utf-8') as f:
        json.dump(best_channels, f, indent=4)

    # Save results to an M3U file
    with open('./best_channels.m3u', 'w', encoding='utf-8') as f:
        for channel_name, best_speed_info in best_channels.items():
            if best_speed_info["speed"] > 0.3 * 1024 * 1024:
                f.write(f"#EXTINF:-1,{best_speed_info['name']}\n"
                        f"{best_speed_info['media_url']}\n")

    logger.info("\nBest channels and bandwidth information have been saved to 'best_channels.m3u'")


if __name__ == "__main__":
    args = arg_parser()
    main(m3u_url=args.url_or_path,
         regex_filter=args.filter)
