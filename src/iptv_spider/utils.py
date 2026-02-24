import json
from pathlib import Path
from argparse import Namespace
import argparse

DEFAULT_CONFIG = {
    "m3u8_url": "https://live.iptv365.org/live.m3u",
    "regex_filter": r'\b(cctv|CCTV)-?(?:[1-9]|1[0-7]|5\+?)\b',
    "output_dir": str(Path.home() / "iptv_spider_output"),
    "log_level": "INFO",
    "speed_threshold_mb": 0.3,  # Minimum speed threshold in MB/s for output
    "speed_limit_mb": 2,  # Speed limit in MB/s for early termination
    "max_retries": 3,  # Maximum retry attempts for network requests
    "request_timeout": 30  # Timeout in seconds for HTTP requests
}


def arg_parser() -> Namespace:
    """
    Parse command-line arguments for the IPTV spider program.

    Returns:
        Namespace: Parsed arguments containing the M3U8 URL/path, filter regex, and output directory.
    """
    parser = argparse.ArgumentParser(
        description="Process an M3U8 playlist by downloading or reading from a local file, "
                    "filtering channel names, and selecting the best-performing URLs."
    )

    # Argument: M3U8 URL or local path
    parser.add_argument(
        "--url_or_path",
        type=str,
        default="https://live.iptv365.org/live.m3u",
        help="URL or local path of the M3U8 playlist file. Defaults to 'https://live.iptv365.org/live.m3u'."
    )

    # Argument: Regular expression filter
    parser.add_argument(
        "--filter",
        type=str,
        default=r'\b(cctv|CCTV)-?(?:[1-9]|1[0-7]|5\+?)\b',
        help="Regex pattern to filter channel names. Defaults to a pattern matching CCTV channels."
    )

    # Argument: Output directory
    parser.add_argument(
        "--output_dir",
        type=str,
        default=".",
        help="Directory where the results (JSON and M3U files) will be saved. Defaults to the current directory."
    )

    # Argument: Speed threshold in MB/s
    parser.add_argument(
        "--speed_threshold_mb",
        type=float,
        default=0.3,
        help="Minimum speed threshold in MB/s for channels to be included in output. Defaults to 0.3 MB/s."
    )

    # Argument: Speed limit in MB/s for early termination
    parser.add_argument(
        "--speed_limit_mb",
        type=float,
        default=2,
        help="Speed limit in MB/s. Testing stops when this speed is reached. Defaults to 2 MB/s."
    )

    # Argument: Maximum retry attempts
    parser.add_argument(
        "--max_retries",
        type=int,
        default=3,
        help="Maximum number of retry attempts for failed network requests. Defaults to 3."
    )

    # Argument: Request timeout
    parser.add_argument(
        "--request_timeout",
        type=int,
        default=30,
        help="Timeout in seconds for HTTP requests. Defaults to 30 seconds."
    )

    return parser.parse_args()


def get_config_dir() -> Path:
    """
    Get the path to the configuration directory.

    Returns:
        Path: Path to the configuration directory (e.g., ~/.iptv-spider).
    """
    config_dir = Path.home() / ".iptv-spider"
    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def save_config(config: dict, file_name: str = "config.json"):
    """
    Save the configuration file.

    Args:
        config (dict): Configuration data to save.
        file_name (str): Name of the configuration file.
    """
    config_path = get_config_dir() / file_name
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def load_config(file_name: str = "config.json") -> dict:
    """
    Load the configuration file.

    Args:
        file_name (str): Name of the configuration file.

    Returns:
        dict: Loaded configuration data.
    """
    config_path = get_config_dir() / file_name
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Create default config if not exists
        save_config(DEFAULT_CONFIG, file_name)
        return DEFAULT_CONFIG
