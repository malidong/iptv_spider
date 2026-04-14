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
from numbers import Number

from iptv_spider.logger import logger
from iptv_spider.m3u import M3U8
from iptv_spider.utils import build_effective_runtime_config, sanitize_runtime_config


def _safe_fps(value: object, default: float = -1.0) -> float:
    if isinstance(value, Number):
        return float(value)
    return default


def main(
    m3u_url: str,
    regex_filter: str,
    output_dir: str,
    speed_threshold_mb: float = 0.3,
    speed_limit_mb: float = 2,
    max_retries: int = 3,
    request_timeout: int = 30,
    epg_url: str = "",
    output_with_epg: bool = False,
    dedup_mode: str = "url_fingerprint",
    dedup_keep: str = "first",
    cache_enabled: bool = True,
    cache_ttl_hours: int = 24,
    cache_file: str = "",
    cache_clear: bool = False,
    probe_timeout: int | None = None,
) -> dict:
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
        speed_threshold_mb (float): Minimum speed threshold in MB/s for output.
        speed_limit_mb (float): Speed limit in MB/s for early termination.
        max_retries (int): Maximum retry attempts for network requests.
        request_timeout (int): Timeout in seconds for HTTP requests.

    Returns:
        dict: Statistics about the test results.
    """
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Output directory created: {output_dir}")

    # Create an M3U8 object and load channels
    logger.info(f"Processing M3U8 playlist from: {m3u_url}")
    m3u8 = M3U8(
        path=m3u_url,
        regex_filter=regex_filter,
        max_retries=max_retries,
        request_timeout=request_timeout,
        probe_timeout=probe_timeout or 10,
        dedup_mode=dedup_mode,
        dedup_keep=dedup_keep,
        cache_enabled=cache_enabled,
        cache_ttl_hours=cache_ttl_hours,
        cache_file=cache_file if cache_file else None,
        cache_clear=cache_clear,
    )

    logger.info(f"Total channels filtered: {len(m3u8.channels)}")
    best_channels_dict = m3u8.get_best_channels(speed_limit=int(speed_limit_mb))

    # Prepare results for saving
    best_channels = {}
    speed_threshold_bytes = speed_threshold_mb * 1024 * 1024
    valid_channels = 0

    for channel_name, channel in best_channels_dict.items():
        if channel.speed > speed_threshold_bytes:
            valid_channels += 1
            metadata = {
                "resolution": getattr(channel, "resolution", "Unknown"),
                "fps": _safe_fps(getattr(channel, "fps", -1.0)),
            }
            probe_metadata = None
            probe_fn = getattr(channel, "get_ffprobe_metadata", None)
            if callable(probe_fn):
                try:
                    probe_metadata = probe_fn()
                except Exception:
                    probe_metadata = None
            if isinstance(probe_metadata, dict):
                metadata["resolution"] = probe_metadata.get(
                    "resolution", metadata["resolution"]
                )
                metadata["fps"] = _safe_fps(probe_metadata.get("fps"), metadata["fps"])

            best_channels[channel_name] = {
                "name": channel.channel_name,
                "meta": channel.meta,
                "media_url": channel.media_url,
                "speed": channel.speed,
                "speed_mbps": round(channel.speed / (1024 * 1024), 2),
                "resolution": metadata["resolution"],
                "fps": metadata["fps"],
                "video_metadata": {
                    "resolution": metadata["resolution"],
                    "fps": metadata["fps"],
                },
            }

    # Save filtered channels to a JSON file
    json_filename = os.path.join(
        output_dir, f"best_channels_{datetime.today().strftime('%Y-%m-%d')}.json"
    )
    with open(json_filename, "w", encoding="utf-8") as json_file:
        json.dump(best_channels, json_file, indent=4, ensure_ascii=False)
    logger.info(f"Filtered channel details saved to: {json_filename}")

    # Save results to an M3U file
    m3u_filename = os.path.join(output_dir, "best_channels.m3u")
    with open(m3u_filename, "w", encoding="utf-8") as m3u_file:
        m3u_file.write(
            f'#EXTM3U url-tvg="{epg_url}"\n'
            if (output_with_epg and epg_url)
            else "#EXTM3U\n"
        )
        for channel_name, channel_info in best_channels.items():
            m3u_file.write(f"{channel_info['meta']},{channel_info['name']}\n")
            m3u_file.write(f"{channel_info['media_url']}\n")
    logger.info(f"Filtered M3U playlist saved to: {m3u_filename}")

    # Calculate and return statistics
    dedup_count = len(m3u8.dedup_trace) if hasattr(m3u8, "dedup_trace") else 0
    stats = {
        "total_channels_filtered": len(m3u8.channels),
        "best_channels_tested": len(best_channels_dict),
        "valid_channels_output": valid_channels,
        "speed_threshold_mb": speed_threshold_mb,
        "deduplicated_count": dedup_count,
        "dedup_trace": m3u8.dedup_trace if hasattr(m3u8, "dedup_trace") else [],
        "output_files": [json_filename, m3u_filename],
    }

    return stats


def entrypoint(argv: list[str] | None = None) -> None:
    """
    Entry point for the IPTV Spider program.
    """
    # Parse command-line arguments and merge with environment defaults.
    config = build_effective_runtime_config(argv=argv)

    # Run the main program with provided arguments
    logger.info("Starting IPTV Spider...")
    logger.info("Runtime config: %s", sanitize_runtime_config(config))
    stats = main(
        m3u_url=str(config.get("url_or_path", "https://live.iptv365.org/live.m3u")),
        regex_filter=str(
            config.get("filter", r"\b(cctv|CCTV)-?(?:[1-9]|1[0-7]|5\+?)\b")
        ),
        output_dir=str(config.get("output_dir", ".")),
        speed_threshold_mb=config.get("speed_threshold_mb", 0.3),
        speed_limit_mb=config.get("speed_limit_mb", 2),
        max_retries=config.get("max_retries", 3),
        request_timeout=config.get("request_timeout", 30),
        epg_url=str(config.get("epg_url", "")),
        output_with_epg=bool(config.get("output_with_epg", False)),
        dedup_mode=str(config.get("dedup_mode", "url_fingerprint")),
        dedup_keep=str(config.get("dedup_keep", "first")),
        cache_enabled=bool(config.get("cache_enabled", True)),
        cache_ttl_hours=int(config.get("cache_ttl_hours", 24)),
        cache_file=str(config.get("cache_file", "")),
        cache_clear=bool(config.get("cache_clear", False)),
        probe_timeout=config.get("probe_timeout"),
    )

    # Log statistics
    logger.info("=" * 50)
    logger.info("IPTV Spider Test Summary:")
    logger.info(f"Total channels filtered: {stats['total_channels_filtered']}")
    logger.info(f"Best channels tested: {stats['best_channels_tested']}")
    logger.info(f"Valid channels output: {stats['valid_channels_output']}")
    logger.info(f"Speed threshold: {stats['speed_threshold_mb']} MB/s")
    logger.info(f"Output files: {', '.join(stats['output_files'])}")
    logger.info("=" * 50)
    logger.info("IPTV Spider finished execution.")


if __name__ == "__main__":
    entrypoint()
