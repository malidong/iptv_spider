# IPTV Spider

[![PyPI Version](https://img.shields.io/pypi/v/iptv-spider.svg)](https://pypi.org/project/iptv-spider/)
[![License](https://img.shields.io/pypi/l/iptv-spider.svg)](https://github.com/yourusername/iptv-spider/blob/main/LICENSE)

**IPTV Spider** is a tool for managing M3U8 playlists, allowing you to download IPTV resources, filter channels based on
specific criteria, and output the best-performing stream for each channel based on speed tests.

---

## 🌟 Features

- **M3U8 File Handling**: Download from a remote URL or read from a local path.
- **Channel Filtering**: Use regular expressions to filter channel names.
- **Speed Test and Optimization**: Automatically test stream speeds and select the best source for each channel.
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

## � Advanced Setup

### Using UV (Recommended for Development)

For an isolated and reproducible build environment, we recommend using [`uv`](https://astral.sh/blog/uv/):

```bash
# Install uv (if not already installed)
pip install uv

# Clone the repository
git clone https://github.com/malidong/iptv_spider.git
cd iptv_spider

# Initialize the environment
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
pytest tests/
```

The project includes 11 comprehensive test cases covering:
- Channel initialization and speed testing
- M3U8 playlist parsing
- Configuration loading and validation
- Speed filtering and output generation

### Code Quality

```bash
# Run flake8 linting
flake8 src/ tests/ --select E,W,F

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
- **pytest**: Unit testing framework (development dependency)
- **flake8**: Code linting (development dependency)

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
