# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
# pylint: disable=broad-exception-caught
"""
Entry module for iptv_spider.

This script downloads and processes an M3U8 playlist, filters channels using a regex pattern,
and outputs the best-performing channels to both a JSON file and an M3U file.
"""

import os

from datetime import datetime
import json

from iptv_spider.m3u import M3U8
from iptv_spider.logger import logger
from iptv_spider.utils import arg_parser, load_config


def main(m3u_url: str, regex_filter: str, output_dir: str):
    """
    Main function to process an IPTV playlist.

    Steps:
    1. Download or read the M3U8 file.
    2. Filter channels by name using the regex pattern.
    3. Select the fastest URL for each unique channel name.
    4. Save results to JSON and M3U files.

    Args:
        m3u_url (str): URL or local path of the M3U8 file.
        regex_filter (str): Regular expression to filter channel names.
        output_dir (str): Directory to save the output files.
    """
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Output directory created: {output_dir}")

    # Create an M3U8 object and load channels
    logger.info(f"Processing M3U8 playlist from: {m3u_url}")
    m3u8: M3U8 = M3U8(path=m3u_url, regex_filter=regex_filter)
    best_channels_dict: dict = m3u8.get_best_channels()

    # Prepare results for saving
    best_channels: dict = {}
    for channel_name, channel in best_channels_dict.items():
        best_channels[channel_name] = {
            "name": channel.channel_name,
            "meta": channel.meta,
            "media_url": channel.media_url,
            "speed": channel.speed,
            "resolution": channel.resolution
        }

    # Save filtered channels to a JSON file
    json_filename: str = os.path.join(output_dir, f"best_channels_{datetime.today().strftime('%Y-%m-%d')}.json")
    with open(json_filename, 'w', encoding='utf-8') as json_file:
        json.dump(best_channels, json_file, indent=4)
    logger.info(f"Filtered channel details saved to: {json_filename}")

    # Save results to an M3U file
    m3u_filename: str = os.path.join(output_dir, 'best_channels.m3u')
    with open(m3u_filename, 'w', encoding='utf-8') as m3u_file:
        for channel_name, channel_info in best_channels.items():
            if channel_info["speed"] > 0.3 * 1024 * 1024:  # Minimum speed threshold: 0.3 MB/s
                m3u_file.write(f"{channel_info['meta']},{channel_info['name']}\n")
                m3u_file.write(f"{channel_info['media_url']}\n")
    logger.info(f"Filtered M3U playlist saved to: {m3u_filename}")


def entrypoint():
    """
    Entry point for the IPTV Spider program.
    """
    # Parse command-line arguments
    args = arg_parser()
    config = load_config()
    config.update(args.__dict__)

    # Run the main program with provided arguments
    logger.info("Starting IPTV Spider...")
    main(
        m3u_url=config.get("url_or_path"),
        regex_filter=config.get("filter"),
        output_dir=config.get("output_dir")
    )
    logger.info("IPTV Spider finished execution.")


if __name__ == "__main__":
    # Parse command-line arguments
    args = arg_parser()
    config = load_config()
    config.update(args.__dict__)

    # Run the main program with provided arguments
    logger.info("Starting IPTV Spider...")
    main(
        m3u_url=args.url_or_path,
        regex_filter=args.filter,
        output_dir=args.output_dir
    )
    logger.info("IPTV Spider finished execution.")
