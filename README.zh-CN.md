# IPTV Spider

[![PyPI 版本](https://img.shields.io/pypi/v/iptv-spider.svg)](https://pypi.org/project/iptv-spider/)
[![许可证](https://img.shields.io/pypi/l/iptv-spider.svg)](https://github.com/malidong/iptv_spider/blob/main/LICENSE)

**IPTV Spider** 是一个 M3U8 播放列表管理工具，可以下载 IPTV 资源、基于用户条件过滤频道，并根据网速测试结果为每个频道选择最佳流源。

---

## 🌟 功能特性

- **M3U8 文件处理**：支持从远程 URL 下载或本地路径读取。
- **频道过滤**：使用正则表达式过滤频道名称。
- **速度测试与优化**：自动测试流媒体速度并为每个频道选择最佳源。
- **智能去重**：基于 URL 指纹去重，避免重复流源。
- **增量测速缓存**：复用近期测速结果，减少重复测试。
- **EPG 关联**：可选在输出 M3U 头部写入 `url-tvg` 节目单源。
- **多格式输出**：
    - 保存为 JSON 文件（包含详细信息）。
    - 生成标准 M3U 播放列表。
- **自定义输出目录**：灵活指定结果保存位置。

---

## 🛠️ 安装

### 通过 pip 安装：

```bash
pip install iptv-spider
```

---

## 🚀 快速开始

### 1️⃣ 基础用法

下载默认 M3U8 文件并过滤最佳 CCTV 频道：

```bash
iptv-spider
```

### 2️⃣ 自定义参数

使用命令行参数自定义操作。例如：

#### 指定 URL 和自定义频道过滤：

```bash
iptv-spider --url_or_path "https://example.com/mylist.m3u" --filter "HBO|ESPN"
```

#### 指定输出目录：

```bash
iptv-spider --output_dir "./results"
```

#### 输出带 EPG 的 M3U：

```bash
iptv-spider --output_with_epg --epg_url "http://epg.51zmt.top:8000/e.xml"
```

#### 去重与缓存控制：

```bash
iptv-spider --dedup_mode url_fingerprint --dedup_keep first --cache_enabled --cache_ttl_hours 24
```

---

## 📋 参数说明

支持以下命令行参数：

| 参数                 | 默认值                                       | 说明                                                       |
|----------------------|----------------------------------------------|----------------------------------------------------------|
| `--url_or_path`      | `https://live.iptv365.org/live.m3u`          | M3U8 文件的 URL 或本地路径。                             |
| `--filter`           | \\b(cctv\|CCTV)-?(?:[1-9]\|1[0-7]\|5\\+?)\\b | 用于过滤频道名称的正则表达式。                           |
| `--output_dir`       | `~/iptv_spider_output`                       | 保存结果的目录。                                        |
| `--speed_threshold_mb` | `0.3`                                        | 输出频道的最小速度阈值（MB/s）。                       |
| `--speed_limit_mb`   | `2.0`                                        | 达到此速度后停止测试的最大速度（MB/s）。               |
| `--max_retries`      | `3`                                          | 网络请求失败的最大重试次数。                           |
| `--request_timeout`  | `30`                                         | HTTP 请求超时时间（秒）。                              |
| `--epg_url`          | `http://epg.51zmt.top:8000/e.xml`            | 可选 EPG 源地址，用于写入 M3U 头部。                   |
| `--output_with_epg`  | `False`                                      | 若提供 EPG 则写入 `#EXTM3U url-tvg="..."` 头部。       |
| `--dedup_mode`       | `url_fingerprint`                            | 去重模式（`url_fingerprint` 或 `none`）。             |
| `--dedup_keep`       | `first`                                      | 去重保留策略（`first` 或 `fastest`）。                 |
| `--cache_enabled`    | `True`                                       | 是否启用测速缓存。                                    |
| `--cache_ttl_hours`  | `24`                                         | 缓存有效期（小时）。                                  |
| `--cache_file`       | `~/.iptv-spider/tested_channels.json`        | 测速缓存文件路径。                                    |
| `--cache_clear`      | `False`                                      | 运行前清空测速缓存。                                  |

---

## 📂 输出文件

运行程序后会生成以下文件：

1. **`best_channels_YYYY-MM-DD.json`**  
   包含过滤后频道的详细信息（名称、元数据、URL、速度、分辨率等）。

2. **`best_channels.m3u`**  
   标准 M3U 播放列表，包含最佳频道，可直接在媒体播放器中使用。

---

## 📜 输出示例

### JSON 文件示例：

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

### M3U 文件示例：

```m3u
#EXTINF:-1 tvg-id="CCTV1.cn" tvg-name="CCTV-1",CCTV-1
http://example.com/cctv1.m3u8
#EXTINF:-1 tvg-id="CCTV5plus.cn" tvg-name="CCTV-5+",CCTV-5+
http://example.com/cctv5plus.m3u8
```

---

## 🛡️ 兼容性

- **Python 版本**：支持 Python 3.11、3.12、3.13 和 3.14+。
- **包管理器**：已测试 `pip`、`uv` 和标准安装方法。
- **平台支持**：Linux、macOS、Windows。
- **依赖项**：
    - `requests`：用于 HTTP 请求。
    - `m3u8`：用于 M3U8 播放列表解析。
    - `argparse`：用于命令行参数解析（内置）。

---

## 📦 高级设置

### 使用 UV（推荐用于开发）

为了获得隔离且可复现的构建环境，建议使用 [`uv`](https://astral.sh/blog/uv/)：

```bash
# 安装 uv（如未安装）
pip install uv

# 克隆仓库
git clone https://github.com/malidong/iptv_spider.git
cd iptv_spider

# 初始化环境
uv sync

# 运行项目
uv run iptv-spider --help
```

**优点**：自动依赖管理、无需全局包安装、更快的设置。

### 传统设置

```bash
# 克隆仓库
git clone https://github.com/malidong/iptv_spider.git
cd iptv_spider

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行项目
python -m iptv_spider.main --help
```

---

## ⚡ 性能优化

项目包含多项性能增强：

- **并行频道测试**：使用 ThreadPoolExecutor 并发测试频道（4 个工作线程），相比串行测试速度提升约 75%。
- **服务器速度缓存**：将已测速的服务器速度保存到 JSON 文件，加快后续运行。
- **重试机制**：对不稳定连接实现自动 3 次重试，采用指数退避策略。
- **可配置参数**：通过命令行参数灵活调整速度阈值、请求超时和重试次数。

### 性能参数

优化设置示例：

```bash
iptv-spider \
  --url_or_path "https://example.com/list.m3u" \
  --filter "CCTV" \
  --speed_threshold_mb 0.5 \
  --speed_limit_mb 5.0 \
  --max_retries 5 \
  --request_timeout 45
```

## 🧪 测试与开发

### 运行测试

```bash
pytest tests/
```

项目包括 11 个全面的测试用例，覆盖：
- 频道初始化与速度测试
- M3U8 播放列表解析
- 配置加载与验证
- 速度过滤与输出生成

### 代码质量检查

```bash
# 运行 flake8 检查
flake8 src/ tests/ --select E,W,F

# 使用 nox 在所有 Python 版本上运行
nox -s tests-3.14  # 在 Python 3.14 上测试
nox -s lint        # 运行 linting
```

### 跨平台测试

推送到 GitHub 时，自动测试会在以下环境运行：
- **Python 版本**：3.11、3.12、3.13、3.14
- **平台**：Ubuntu、macOS、Windows

---

## 🔨 项目依赖

- **ffprobe**：用于检测流媒体分辨率（FFmpeg 的一部分）
- **m3u8**：M3U8 播放列表格式解析
- **requests**：用于下载 M3U8 文件和测试流媒体的 HTTP 请求
- **pytest**：单元测试框架（测试依赖）
- **flake8**：代码 Linting（开发依赖）

---

## ✨ 最新更新

- ✅ **EPG 支持**：可选在 M3U 头部注入 `url-tvg`。
- ✅ **URL 指纹去重**：基于规范化 URL 去重。
- ✅ **增量测速缓存**：复用近期测速结果，加速运行。

---

## ✨ 最新改进（v0.3.0+）

此版本包含重大改进：

- ✅ **参数化配置**：所有硬编码值现已通过 CLI 配置
- ✅ **并行测试**：频道速度测试速度提升约 75%
- ✅ **持久化缓存**：服务器速度缓存保存到 JSON，加快后续运行
- ✅ **重试逻辑**：网络故障时自动 3 次重试机制
- ✅ **统计报告**：详细的测试频道和过滤结果指标
- ✅ **类型注解**：完整的代码类型提示
- ✅ **资源管理**：网络连接的正确清理
- ✅ **完整测试**：11 个覆盖所有主要组件的单元测试

---

## 📝 待办事项

- ✅ 添加测试服务器速度保存和重用功能。
- ✅ 实现不可靠服务器的黑名单。
- ⏳ 更有效地处理 HTTP-to-UDP 和 HTTP-to-RTP 流。
- ⏳ 添加对其他播放列表格式的支持（如 .xml、.txt）。
- ⏳ 构建图形用户界面 (GUI)？

---

## 🤝 贡献指南

欢迎以任何形式贡献，包括：

- 报告 Bug
- 请求新功能
- 改进文档或代码

### 设置开发环境

1. **克隆仓库**：
   ```bash
   git clone https://github.com/malidong/iptv_spider.git
   cd iptv_spider
   ```

2. **使用 UV 设置**（推荐）：
   ```bash
   # 安装 uv（如需要）
   pip install uv
   
   # 初始化环境并安装依赖
   uv sync
   ```

3. **或使用传统方法设置**：
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **运行测试**：
   ```bash
   pytest tests/
   ```

5. **检查代码质量**：
   ```bash
   nox -s lint  # 运行 flake8
   ```

---

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE.txt)。

---

## 🔗 项目链接

- **GitHub**：[malidong/iptv_spider](https://github.com/malidong/iptv_spider)
- **PyPI**：[iptv-spider](https://pypi.org/project/iptv-spider/)
- **问题报告**：[GitHub Issues](https://github.com/malidong/iptv_spider/issues)
