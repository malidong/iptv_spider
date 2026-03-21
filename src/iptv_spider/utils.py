import json
import hashlib
from pathlib import Path
from argparse import Namespace
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import argparse
from datetime import datetime, timezone

DEFAULT_CONFIG = {
    "m3u8_url": "https://live.iptv365.org/live.m3u",
    "regex_filter": r'\b(cctv|CCTV)-?(?:[1-9]|1[0-7]|5\+?)\b',
    "output_dir": str(Path.home() / "iptv_spider_output"),
    "log_level": "INFO",
    "speed_threshold_mb": 0.3,  # Minimum speed threshold in MB/s for output
    "speed_limit_mb": 2,  # Speed limit in MB/s for early termination
    "max_retries": 3,  # Maximum retry attempts for network requests
    "request_timeout": 30,  # Timeout in seconds for HTTP requests
    "epg_url": "http://epg.51zmt.top:8000/e.xml",
    "output_with_epg": False,
    "dedup_mode": "url_fingerprint",
    "dedup_keep": "first",
    "cache_enabled": True,
    "cache_ttl_hours": 24,
    "cache_file": str(Path.home() / ".iptv-spider" / "tested_channels.json"),
    "cache_clear": False,
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

    # Argument: EPG URL
    parser.add_argument(
        "--epg_url",
        type=str,
        default="http://epg.51zmt.top:8000/e.xml",
        help="Optional EPG URL to embed into output M3U header."
    )

    # Argument: Output M3U with EPG header
    parser.add_argument(
        "--output_with_epg",
        action="store_true",
        help="Write M3U header with EPG url-tvg when epg_url is provided."
    )

    # Argument: Dedup mode
    parser.add_argument(
        "--dedup_mode",
        type=str,
        default="url_fingerprint",
        choices=["url_fingerprint", "none"],
        help="Deduplication mode. Defaults to url_fingerprint."
    )

    # Argument: Dedup keep strategy
    parser.add_argument(
        "--dedup_keep",
        type=str,
        default="first",
        choices=["first", "fastest"],
        help="Deduplication keep strategy. Defaults to first."
    )

    # Argument: Cache enabled
    parser.add_argument(
        "--cache_enabled",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable or disable speed cache."
    )

    # Argument: Cache TTL hours
    parser.add_argument(
        "--cache_ttl_hours",
        type=int,
        default=24,
        help="Cache TTL in hours. Defaults to 24."
    )

    # Argument: Cache file
    parser.add_argument(
        "--cache_file",
        type=str,
        default=str(Path.home() / ".iptv-spider" / "tested_channels.json"),
        help="Path to speed cache file."
    )

    parser.add_argument(
        "--cache_clear",
        action="store_true",
        help="Clear speed cache before run."
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


def normalize_url(url: str) -> str:
    """
    Normalize URL for fingerprinting.

    - Lowercase scheme and host
    - Remove fragment
    - Sort query parameters
    """
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    scheme = parsed.scheme.lower()
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
    normalized = parsed._replace(
        scheme=scheme,
        netloc=netloc,
        query=query,
        fragment=""
    )
    return urlunparse(normalized)


def url_fingerprint(url: str) -> str:
    """
    Generate a stable fingerprint for a URL.
    """
    normalized = normalize_url(url)
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    """
    Return current UTC time in ISO format.
    """
    return datetime.now(timezone.utc).isoformat()
