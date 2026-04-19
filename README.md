# IPTV Spider

[![PyPI Version](https://img.shields.io/pypi/v/iptv-spider.svg)](https://pypi.org/project/iptv-spider/)
[![License](https://img.shields.io/pypi/l/iptv-spider.svg)](https://github.com/malidong/iptv_spider/blob/main/LICENSE.txt)

**IPTV Spider** is a tool for managing M3U8 playlists, allowing you to download IPTV resources, filter channels based on
specific criteria, and output the best-performing stream for each channel based on speed tests.

---

## 🌟 Features

- **M3U8 File Handling**: Download from a remote URL or read from a local path.
- **Channel Filtering**: Use regular expressions to filter channel names.
- **Speed Test and Optimization**: Automatically test stream speeds and select the best source for each channel.
- **Smart Deduplication**: Deduplicate by URL fingerprint to avoid duplicate streams.
- **Incremental Speed Cache**: Reuse recent speed test results to reduce repeated testing.
- **EPG Integration**: Optionally embed `url-tvg` EPG source in the output M3U header.
- **Multi-format Output**:
    - Save results as a JSON file.
    - Generate a standard M3U playlist with the best channels.
- **Customizable Output Directory**: Specify where to save the results flexibly.

---

## 🛠️ Installation

### Install via pip:

```bash
pip install iptv-spider
```

---

## 🚀 Quick Start

### 1️⃣ Basic Usage

Download the M3U8 file from the default URL and filter the best-performing CCTV channels:

```bash
iptv-spider
```

### 2️⃣ Custom Parameters

You can customize operations using command-line arguments. For example:

#### Specify URL and Custom Channel Filters:

```bash
iptv-spider --url_or_path "https://example.com/mylist.m3u" --filter "HBO|ESPN"
```

#### Specify Output Directory:

```bash
iptv-spider --output_dir "./results"
```

#### Enable EPG in Output:

```bash
iptv-spider --output_with_epg --epg_url "http://epg.51zmt.top:8000/e.xml"
```

#### Control Deduplication & Cache:

```bash
iptv-spider --dedup_mode url_fingerprint --dedup_keep first --cache_enabled --cache_ttl_hours 24
```

#### Run Health Check:

```bash
iptv-spider --health
iptv-spider --health --verbose
IPTV_HEALTH_CHECK_NETWORK=0 iptv-spider --health  # Skip network check
```

### 3️⃣ Run With Docker Compose

```bash
# 1) Prepare env file
cp .env.example .env

# 2) (Optional) edit .env for your source/filter/output paths

# 3) Build and run
docker compose up --build
```

Default mount points:
- `./input -> /data/input`
- `./output -> /data/output`
- `./cache -> /data/cache`
- `./logs -> /data/logs`

You can change host paths with:
- `HOST_INPUT_DIR`
- `HOST_OUTPUT_DIR`
- `HOST_CACHE_DIR`
- `HOST_LOG_DIR`

---

## 📋 Parameters

The following command-line arguments are supported:

| Parameter            | Default Value                                | Description                                                      |
|----------------------|----------------------------------------------|------------------------------------------------------------------|
| `--url_or_path`      | `https://live.iptv365.org/live.m3u`          | URL or local path of the M3U8 file.                              |
| `--filter`           | \\b(cctv\|CCTV)-?(?:[1-9]\|1[0-7]\|5\\+?)\\b | Regular expression for filtering channel names.                  |
| `--output_dir`       | `~/iptv_spider_output`                       | Directory to save the results.                                   |
| `--speed_threshold_mb` | `0.3`                                        | Minimum acceptable speed (MB/s) for output.                      |
| `--speed_limit_mb`   | `2.0`                                        | Maximum speed (MB/s) for early termination.                      |
| `--max_retries`      | `3`                                          | Maximum retry attempts per network request.                      |
| `--request_timeout`  | `30`                                         | HTTP request timeout in seconds.                                 |
| `--epg_url`          | `http://epg.51zmt.top:8000/e.xml`            | Optional EPG URL to embed into M3U header.                        |
| `--output_with_epg`  | `False`                                      | Write `#EXTM3U url-tvg="..."` header when EPG is provided.        |
| `--dedup_mode`       | `url_fingerprint`                            | Deduplication mode (`url_fingerprint` or `none`).                |
| `--dedup_keep`       | `first`                                      | Deduplication keep strategy (`first` or `fastest`).               |
| `--cache_enabled`    | `True`                                       | Enable speed cache.                                              |
| `--cache_ttl_hours`  | `24`                                         | Cache TTL in hours.                                              |
| `--cache_file`       | `~/.iptv-spider/tested_channels.json`        | Path to speed cache file.                                        |
| `--cache_clear`      | `False`                                      | Clear speed cache before run.                                    |
| `--health`         | `False`                                      | Run health check and exit.                                    |
| `--verbose`        | `False`                                      | Enable verbose output (used with --health).                         |

---

## 📂 Output Files

After running the program, the following files will be generated:

1. **`best_channels_YYYY-MM-DD.json`**  
   Contains detailed information about the filtered channels (e.g., name, metadata, URL, speed, resolution).

2. **`best_channels.m3u`**  
   A standard M3U playlist with the best-performing channels, ready for use in media players.

---

## 📜 Example Output

### JSON File:

```json
{
  "CCTV-1": {
    "name": "CCTV-1",
    "meta": "#EXTINF:-1 tvg-id=\"CCTV1.cn\" tvg-name=\"CCTV-1\"",
    "media_url": "http://example.com/cctv1.m3u8",
    "speed": 1048576,
    "resolution": "1920x1080"
  },
  "CCTV-5+": {
    "name": "CCTV-5+",
    "meta": "#EXTINF:-1 tvg-id=\"CCTV5plus.cn\" tvg-name=\"CCTV-5+\"",
    "media_url": "http://example.com/cctv5plus.m3u8",
    "speed": 2048576,
    "resolution": "1920x1080"
  }
}
```

### M3U File:

```m3u
#EXTINF:-1 tvg-id="CCTV1.cn" tvg-name="CCTV-1",CCTV-1
http://example.com/cctv1.m3u8
#EXTINF:-1 tvg-id="CCTV5plus.cn" tvg-name="CCTV-5+",CCTV-5+
http://example.com/cctv5plus.m3u8
```

---

## 🛡️ Compatibility

- **Python Version**: Supports Python 3.11, 3.12, 3.13, and 3.14+.
- **Package Manager**: Tested with `pip`, `uv`, and standard installation methods.
- **Platforms**: Linux, macOS, Windows.
- **Dependencies**:
    - `requests`: For HTTP requests.
    - `m3u8`: For M3U8 playlist parsing.
    - `argparse`: For parsing command-line arguments (built-in).

---

## 🧰 Advanced Setup

### Using UV (Recommended for Development)

For an isolated and reproducible build environment, we recommend using [`uv`](https://astral.sh/blog/uv/):

```bash
# Install uv (if not already installed)
pip install uv

# Clone the repository
git clone https://github.com/malidong/iptv_spider.git
cd iptv_spider

# Initialize the environment (creates/updates .venv)
uv sync

# Run the project
uv run iptv-spider --help
```

**Benefits**: Automatic dependency management, no global packages installation needed, faster setup.

### Traditional Setup

```bash
# Clone the repository
git clone https://github.com/malidong/iptv_spider.git
cd iptv_spider

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)

# Install dependencies
pip install -r requirements.txt

# Run the project
python -m iptv_spider.main --help
```

---

## ⚡ Performance Optimizations

The project includes several performance enhancements:

- **Parallel Channel Testing**: Tests multiple channels concurrently (ThreadPoolExecutor with 4 workers) instead of sequentially, resulting in ~75% speedup.
- **Server Speed Caching**: Persists tested server speeds to JSON for faster subsequent runs.
- **Retry Mechanism**: Implements automatic 3-retry logic with exponential backoff for unreliable connections.
- **Configurable Parameters**: Fine-tune speed thresholds, request timeouts, and retry attempts via command-line arguments.

### Performance Parameters

Example with optimized settings:

```bash
iptv-spider \
  --url_or_path "https://example.com/list.m3u" \
  --filter "CCTV" \
  --speed_threshold_mb 0.5 \
  --speed_limit_mb 5.0 \
  --max_retries 5 \
  --request_timeout 45
```

---

## 🧪 Testing & Development

### Run Tests

```bash
# With UV (recommended)
uv sync --extra test
uv run pytest tests/
```

The project includes 91 comprehensive test cases covering:
- Channel initialization and speed testing
- M3U8 playlist parsing
- Configuration loading and validation
- Speed filtering and output generation

### Code Quality

```bash
# With UV (recommended)
uv sync --extra dev
uv run flake8 src/ tests/ --select E,W,F

# Run with nox for all Python versions
nox -s tests-3.14  # Test with Python 3.14
nox -s lint        # Run linting
```

### Cross-Platform Testing

When pushing to GitHub, automated tests run on:
- **Python**: 3.11, 3.12, 3.13, 3.14
- **Platforms**: Ubuntu, macOS, Windows

---

## 🔨 Project Dependencies

- **ffprobe**: Required to detect stream resolution (part of FFmpeg)
- **m3u8**: M3U8 playlist format parsing
- **requests**: HTTP requests for downloading M3U8 files and testing streams
- **pytest**: Unit testing framework (test dependency)
- **flake8**: Code linting (development dependency)
 
---

## ✨ Recent Updates

- ✅ **EPG Support**: Optional `url-tvg` injection into M3U output header.
- ✅ **URL Fingerprint Dedup**: Deduplicate duplicate streams by normalized URL.
- ✅ **Incremental Speed Cache**: Reuse recent speed test results to speed up runs.
- ✅ **Error Tracking**: RunStats and RunError dataclasses for error tracking.
- ✅ **Error Categorization**: Errors categorized as transient vs permanent with actionable logging.
- ✅ **Observability Baseline**: Structured logging (JSON), health checks, run IDs for tracing.

---

## ✨ Recent Improvements (v0.3.0+)

This version includes significant enhancements:

- ✅ **Parameterized Configuration**: All hardcoded values now configurable via CLI
- ✅ **Parallel Testing**: ~75% faster channel speed testing with concurrent execution
- ✅ **Persistent Caching**: Server speed cache saved to JSON for faster reruns
- ✅ **Retry Logic**: Automatic 3-retry mechanism for network failures
- ✅ **Statistics Reporting**: Detailed metrics on tested channels and filtered results
- ✅ **Type Annotations**: Full type hints throughout codebase
- ✅ **Resource Management**: Proper cleanup of network connections
- ✅ **Comprehensive Tests**: 11 unit test cases covering all major components

---

## 📝 To-Do List

- ✅ Add functionality to save tested server speeds and reuse them.
- ✅ Implement blacklist for unreliable servers.
- ⏳ Handle HTTP-to-UDP and HTTP-to-RTP streams more effectively.
- ⏳ Add support for additional playlist formats (e.g., .xml, .txt).
- ⏳ Build a graphical user interface (GUI) for easier usage?

---

## 🤝 Contributing

Contributions are welcome in any form, including:

- Reporting bugs
- Requesting features
- Improving documentation or code

### Setting Up the Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/malidong/iptv_spider.git
   cd iptv_spider
   ```

2. **Setup with UV** (recommended):
   ```bash
   # Install uv if needed
   pip install uv
   
   # Initialize environment and install dependencies
   uv sync
   ```

3. **Or setup traditionally**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Run tests**:
   ```bash
   pytest tests/
   ```

5. **Check code quality**:
   ```bash
   nox -s lint  # Run flake8
   ```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE.txt).

---

## 🔗 Project Links

- **GitHub**: [malidong/iptv_spider](https://github.com/malidong/iptv_spider)
- **PyPI**: [iptv-spider](https://pypi.org/project/iptv-spider/)
- **Bug Reports**: [GitHub Issues](https://github.com/malidong/iptv_spider/issues)
