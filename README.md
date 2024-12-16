# IPTV Spider

[![PyPI Version](https://img.shields.io/pypi/v/iptv-spider.svg)](https://pypi.org/project/iptv-spider/)
[![License](https://img.shields.io/pypi/l/iptv-spider.svg)](https://github.com/malidong/iptv-spider/blob/main/LICENSE)

**IPTV Spider** 是一个工具，用于处理 M3U8 播放列表，通过下载 IPTV 资源，筛选符合条件的频道，并根据测速结果输出最佳的播放源。

---

## 🌟 功能特性

- **M3U8 文件下载**：支持从远程 URL 下载或从本地路径读取 M3U8 文件。
- **频道筛选**：使用正则表达式筛选频道名称。
- **测速与排序**：自动测速并选取每个频道中最优的播放源。
- **多格式输出**：
    - 保存筛选结果为 JSON 文件。
    - 输出最优的频道到标准 M3U 播放列表文件。
- **支持自定义输出目录**：灵活指定结果保存路径。

---

## 🛠️ 安装

### 使用 pip 安装：

```bash
pip install iptv-spider
```

---

## 🚀 快速开始

### 1️⃣ 基本用法

从默认的 URL 下载 M3U8 文件，并筛选出速度最优的 CCTV 频道：

```bash
iptv-spider
```

### 2️⃣ 自定义参数

你可以使用命令行参数自定义操作，例如：

#### 指定 URL 和自定义频道筛选：

```bash
iptv-spider --url_or_path "https://example.com/mylist.m3u" --filter "HBO|ESPN"
```

#### 指定输出目录：

```bash
iptv-spider --output_dir "./results"
```

---

## 📋 参数说明

以下是支持的命令行参数：

| 参数名称            | 默认值                                 | 描述                    |
|-----------------|-------------------------------------|-----------------------|
| `--url_or_path` | `https://live.iptv365.org/live.m3u` | 远程 URL 或本地 M3U8 文件路径。 |
| `--filter`      | `\b(cctv                            | CCTV)-?(?:[1-9]       |1[0-7]|5\+?)\b`             | 用于筛选频道名称的正则表达式。                                                       |
| `--output_dir`  | `.`                                 | 结果保存的目录，默认当前目录。       |

---

## 📂 输出文件

运行程序后，以下文件将生成：

1. **`best_channels_YYYY-MM-DD.json`**  
   包含筛选频道的详细信息（如名称、元数据、播放地址、测速结果等）。

2. **`best_channels.m3u`**  
   标准 M3U 文件，包含测速最优的频道及播放地址，便于在播放器中直接使用。

---

## 📜 示例输出

### JSON 文件内容：

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

### M3U 文件内容：

```m3u
#EXTINF:-1 tvg-id="CCTV1.cn" tvg-name="CCTV-1",CCTV-1
http://example.com/cctv1.m3u8
#EXTINF:-1 tvg-id="CCTV5plus.cn" tvg-name="CCTV-5+",CCTV-5+
http://example.com/cctv5plus.m3u8
```

---

## 🛡️ 兼容性

- **Python 版本**：支持 Python 3.11 及以上。
- **依赖库**：
    - `requests`：用于 HTTP 请求。
    - `argparse`：用于命令行参数解析。

---

## 🤝 贡献

欢迎任何形式的贡献，包括但不限于以下内容：

- 报告 Bug
- 提交功能请求
- 改进文档或代码

### 开发环境配置：

1. 克隆项目到本地：
   ```bash
   git clone https://github.com/malidong/iptv-spider.git
   cd iptv-spider
   ```

2. 创建虚拟环境并安装依赖：
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. 运行测试：
   ```bash
   pytest
   ```

---

## 📄 License

本项目遵循 [MIT License](https://github.com/malidong/iptv-spider/blob/main/LICENSE) 许可。

---

## 🔗 更多信息

- **源码地址**: [GitHub](https://github.com/malidong/iptv-spider)
- **PyPI 页面**: [PyPI](https://pypi.org/project/iptv-spider/)
