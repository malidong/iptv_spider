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

| Parameter       | Default Value                                | Description                                                       |
|-----------------|----------------------------------------------|-------------------------------------------------------------------|
| `--url_or_path` | `https://live.iptv365.org/live.m3u`          | URL or local path of the M3U8 file.                               |
| `--filter`      | \\b(cctv\|CCTV)-?(?:[1-9]\|1[0-7]\|5\\+?)\\b | Regular expression for filtering channel names.                   |
| `--output_dir`  | `.`                                          | Directory to save the results, defaults to the current directory. |

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

- **Python Version**: Compatible with Python 3.11 and above.
- **Dependencies**:
    - `requests`: For HTTP requests.
    - `argparse`: For parsing command-line arguments.

---

## 🔨 Dependencies

    • ffprobe: To get the resolution of the stream.

---

## 📝 To-Do List

	•	Add functionality to save tested server speeds and reuse them. ☑️
	•	Implement blacklist for unreliable servers. ☑️
	•	Handle HTTP-to-UDP and HTTP-to-RTP streams more effectively.
	•	Add support for additional playlist formats (e.g., .xml, .txt). 
	•	Build a graphical user interface (GUI) for easier usage?

---

## 🤝 Contributing

Contributions are welcome in any form, including:

- Reporting bugs
- Requesting features
- Improving documentation or code

### Setting Up the Development Environment:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/iptv-spider.git
   cd iptv-spider
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Run tests:
   ```bash
   pytest
   ```

---

## 📄 License

This project is licensed under the [MIT License](https://github.com/yourusername/iptv-spider/blob/main/LICENSE).

---

## 🔗 More Information

- **Source Code**: [GitHub](https://github.com/yourusername/iptv-spider)
- **PyPI Page**: [PyPI](https://pypi.org/project/iptv-spider/)
