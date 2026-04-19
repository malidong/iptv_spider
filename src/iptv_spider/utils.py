import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from argparse import Namespace
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


RUNTIME_DEFAULTS = {
    "url_or_path": "https://live.iptv365.org/live.m3u",
    "filter": r"\b(cctv|CCTV)-?(?:[1-9]|1[0-7]|5\+?)\b",
    "output_dir": ".",
    "speed_threshold_mb": 0.3,
    "speed_limit_mb": 2,
    "max_retries": 3,
    "request_timeout": 30,
    "epg_url": "http://epg.51zmt.top:8000/e.xml",
    "output_with_epg": False,
    "dedup_mode": "url_fingerprint",
    "dedup_keep": "first",
    "cache_enabled": True,
    "cache_ttl_hours": 24,
    "cache_file": str(Path.home() / ".iptv-spider" / "tested_channels.json"),
    "cache_clear": False,
    "probe_timeout": None,
}

DEFAULT_CONFIG = {
    "m3u8_url": "https://live.iptv365.org/live.m3u",
    "url_or_path": "https://live.iptv365.org/live.m3u",
    "regex_filter": r'\b(cctv|CCTV)-?(?:[1-9]|1[0-7]|5\+?)\b',
    "filter": r'\b(cctv|CCTV)-?(?:[1-9]|1[0-7]|5\+?)\b',
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
    "probe_timeout": None,
}

_SENSITIVE_KEY_PARTS = (
    "token",
    "secret",
    "password",
    "api_key",
    "apikey",
    "auth",
    "bearer",
)

_ENV_ALIASES = {
    "url_or_path": ("IPTV_SPIDER_URL_OR_PATH", "IPTV_SPIDER_M3U8_URL", "IPTV_SPIDER_M3U_URL"),
    "filter": ("IPTV_SPIDER_FILTER", "IPTV_SPIDER_REGEX_FILTER"),
    "output_dir": ("IPTV_SPIDER_OUTPUT_DIR",),
    "speed_threshold_mb": ("IPTV_SPIDER_SPEED_THRESHOLD_MB",),
    "speed_limit_mb": ("IPTV_SPIDER_SPEED_LIMIT_MB",),
    "max_retries": ("IPTV_SPIDER_MAX_RETRIES",),
    "request_timeout": ("IPTV_SPIDER_REQUEST_TIMEOUT",),
    "epg_url": ("IPTV_SPIDER_EPG_URL",),
    "output_with_epg": ("IPTV_SPIDER_OUTPUT_WITH_EPG",),
    "dedup_mode": ("IPTV_SPIDER_DEDUP_MODE",),
    "dedup_keep": ("IPTV_SPIDER_DEDUP_KEEP",),
    "cache_enabled": ("IPTV_SPIDER_CACHE_ENABLED",),
    "cache_ttl_hours": ("IPTV_SPIDER_CACHE_TTL_HOURS",),
    "cache_file": ("IPTV_SPIDER_CACHE_FILE",),
    "cache_clear": ("IPTV_SPIDER_CACHE_CLEAR",),
    "probe_timeout": ("IPTV_SPIDER_PROBE_TIMEOUT",),
}


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Cannot parse boolean value from {value!r}")


def _parse_int(value: Any) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return int(str(value).strip())


def _parse_float(value: Any) -> float:
    if isinstance(value, float):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return float(value)
    return float(str(value).strip())


def _parse_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return _parse_int(value)


def _option_string_to_dest_map(parser: argparse.ArgumentParser) -> dict[str, str]:
    option_map: dict[str, str] = {}
    for action in parser._actions:
        for option_string in action.option_strings:
            option_map[option_string] = action.dest
    return option_map


def _provided_cli_dests(argv: Sequence[str], parser: argparse.ArgumentParser) -> set[str]:
    option_map = _option_string_to_dest_map(parser)
    provided: set[str] = set()
    for token in argv:
        if token == "--":
            break
        if not token.startswith("-"):
            continue
        option_name = token.split("=", 1)[0]
        dest = option_map.get(option_name)
        if dest:
            provided.add(dest)
    return provided


def _normalize_runtime_config(config: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(config)
    url_or_path = normalized.get("url_or_path", normalized.get("m3u8_url", RUNTIME_DEFAULTS["url_or_path"]))
    filter_value = normalized.get("filter", normalized.get("regex_filter", RUNTIME_DEFAULTS["filter"]))
    normalized["url_or_path"] = url_or_path
    normalized["m3u8_url"] = url_or_path
    normalized["filter"] = filter_value
    normalized["regex_filter"] = filter_value
    normalized.setdefault("probe_timeout", None)
    return normalized


def _load_env_config(environ: Mapping[str, str]) -> dict[str, Any]:
    env_config: dict[str, Any] = {}
    parsers = {
        "url_or_path": str,
        "filter": str,
        "output_dir": str,
        "speed_threshold_mb": _parse_float,
        "speed_limit_mb": _parse_float,
        "max_retries": _parse_int,
        "request_timeout": _parse_int,
        "epg_url": str,
        "output_with_epg": _parse_bool,
        "dedup_mode": str,
        "dedup_keep": str,
        "cache_enabled": _parse_bool,
        "cache_ttl_hours": _parse_int,
        "cache_file": str,
        "cache_clear": _parse_bool,
        "probe_timeout": _parse_optional_int,
    }

    for key, env_names in _ENV_ALIASES.items():
        for env_name in env_names:
            if env_name in environ:
                env_config[key] = parsers[key](environ[env_name])
                break

    return _normalize_runtime_config(env_config)


def build_effective_runtime_config(
    argv: Sequence[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """
    Build the runtime configuration using CLI > ENV > defaults precedence.
    """
    parser = _build_arg_parser()
    argv_list = list(sys.argv[1:] if argv is None else argv)
    parsed_args = parser.parse_args(argv_list)
    cli_dests = _provided_cli_dests(argv_list, parser)
    env_source = os.environ if environ is None else environ

    effective = dict(RUNTIME_DEFAULTS)
    effective.update(_load_env_config(env_source))

    for dest in cli_dests:
        if hasattr(parsed_args, dest):
            effective[dest] = getattr(parsed_args, dest)

    return _normalize_runtime_config(effective)


def sanitize_runtime_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """
    Return a logging-safe config view with sensitive fields removed.
    """
    sanitized: dict[str, Any] = {}
    for key, value in config.items():
        lowered = key.lower()
        if any(part in lowered for part in _SENSITIVE_KEY_PARTS):
            continue
        sanitized[key] = value
    return sanitized


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Process an M3U8 playlist by downloading or reading from a local file, "
                    "filtering channel names, and selecting the best-performing URLs."
    )

    parser.add_argument(
        "--url_or_path",
        type=str,
        default=RUNTIME_DEFAULTS["url_or_path"],
        help="URL or local path of the M3U8 playlist file. Defaults to 'https://live.iptv365.org/live.m3u'."
    )

    parser.add_argument(
        "--filter",
        type=str,
        default=RUNTIME_DEFAULTS["filter"],
        help="Regex pattern to filter channel names. Defaults to a pattern matching CCTV channels."
    )

    parser.add_argument(
        "--output_dir",
        type=str,
        default=RUNTIME_DEFAULTS["output_dir"],
        help="Directory where the results (JSON and M3U files) will be saved. Defaults to the current directory."
    )

    parser.add_argument(
        "--speed_threshold_mb",
        type=float,
        default=RUNTIME_DEFAULTS["speed_threshold_mb"],
        help="Minimum speed threshold in MB/s for channels to be included in output. Defaults to 0.3 MB/s."
    )

    parser.add_argument(
        "--speed_limit_mb",
        type=float,
        default=RUNTIME_DEFAULTS["speed_limit_mb"],
        help="Speed limit in MB/s. Testing stops when this speed is reached. Defaults to 2 MB/s."
    )

    parser.add_argument(
        "--max_retries",
        type=int,
        default=RUNTIME_DEFAULTS["max_retries"],
        help="Maximum number of retry attempts for failed network requests. Defaults to 3."
    )

    parser.add_argument(
        "--request_timeout",
        type=int,
        default=RUNTIME_DEFAULTS["request_timeout"],
        help="Timeout in seconds for HTTP requests. Defaults to 30 seconds."
    )

    parser.add_argument(
        "--epg_url",
        type=str,
        default=RUNTIME_DEFAULTS["epg_url"],
        help="Optional EPG URL to embed into output M3U header."
    )

    parser.add_argument(
        "--output_with_epg",
        action="store_true",
        help="Write M3U header with EPG url-tvg when epg_url is provided."
    )

    parser.add_argument(
        "--dedup_mode",
        type=str,
        default=RUNTIME_DEFAULTS["dedup_mode"],
        choices=["url_fingerprint", "none"],
        help="Deduplication mode. Defaults to url_fingerprint."
    )

    parser.add_argument(
        "--dedup_keep",
        type=str,
        default=RUNTIME_DEFAULTS["dedup_keep"],
        choices=["first", "fastest"],
        help="Deduplication keep strategy. Defaults to first."
    )

    parser.add_argument(
        "--cache_enabled",
        action=argparse.BooleanOptionalAction,
        default=RUNTIME_DEFAULTS["cache_enabled"],
        help="Enable or disable speed cache."
    )

    parser.add_argument(
        "--cache_ttl_hours",
        type=int,
        default=RUNTIME_DEFAULTS["cache_ttl_hours"],
        help="Cache TTL in hours. Defaults to 24."
    )

    parser.add_argument(
        "--cache_file",
        type=str,
        default=RUNTIME_DEFAULTS["cache_file"],
        help="Path to speed cache file."
    )

    parser.add_argument(
        "--cache_clear",
        action="store_true",
        help="Clear speed cache before run."
    )

    parser.add_argument(
        "--probe_timeout",
        type=_parse_optional_int,
        default=RUNTIME_DEFAULTS["probe_timeout"],
        help="ffprobe timeout in seconds. Defaults to disabled/auto (None)."
    )

    parser.add_argument(
        "--health",
        action="store_true",
        help="Run health check and exit."
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output."
    )

    return parser


def arg_parser(argv: Sequence[str] | None = None) -> Namespace:
    """
    Parse command-line arguments for the IPTV spider program.

    Returns:
        Namespace: Parsed arguments containing the M3U8 URL/path, filter regex, and output directory.
    """
    parser = _build_arg_parser()
    return parser.parse_args(argv)


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
            return _normalize_runtime_config({**DEFAULT_CONFIG, **json.load(f)})
    else:
        # Create default config if not exists
        save_config(DEFAULT_CONFIG, file_name)
        return _normalize_runtime_config(DEFAULT_CONFIG)


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
