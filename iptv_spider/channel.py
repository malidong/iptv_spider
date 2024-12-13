import requests
import subprocess
import time
import m3u8
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

# 伪装为 PotPlayer 的 User-Agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
}


class Channel:
    __slots__ = ("meta",
                 "channel_name",
                 "media_url",
                 "is_direct",
                 "speed",
                 "resolution")

    def __init__(self, meta: str, channel_name: str, media_url: str):
        self.meta = meta
        self.channel_name = channel_name
        self.media_url = media_url
        self.is_direct = False if media_url.endswith("m3u") or media_url.endswith("m3u8") else True
        self.speed = None
        self.resolution = None

    def get_speed(self) -> float:
        """
        :return: speed of this channel
        """
        print(f"{self.channel_name} 正在测试下载: {self.media_url}")
        if self.is_direct:
            self.speed = self.__test_direct_bandwidth()
        else:
            self.speed = self.__test_m3u8_bandwidth()
        print(f"测试频道速度结束: {self.speed}")
        return self.speed

    def get_video_resolution(self, ts_url: str) -> str:
        """
        Get resolution of the ts_url
        :param ts_url: if ts_url is None, will use self.url
        :return:
        """
        try:
            command = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=p=0",
                ts_url
            ]
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                resolution = result.stdout.strip()
                return resolution if resolution else None
            else:
                return "获取分辨率失败"
        except subprocess.TimeoutExpired:
            print(f"错误: 获取视频分辨率超时 - {ts_url}")
        except Exception as e:
            print(f"错误: 获取视频分辨率时发生异常 - {str(e)}")
        return "未知分辨率"

    def __test_m3u8_bandwidth(self, max_ts: int = 5, max_workers: int = 2) -> float:
        """
        下载并测试每个M3U8内TS文件的带宽
        :param max_ts: Max ts file to test
        :param max_workers: the max number of processes
        :return:
        """
        try:
            # 下载并解析 M3U8 文件
            m3u8_content = requests.get(self.media_url, headers=HEADERS, timeout=10).text
            playlist = m3u8.loads(m3u8_content)

            # 获取 TS 文件链接
            ts_urls = [segment.uri for segment in playlist.segments]
            if not ts_urls:
                return 0

            # 只测试前 max_ts 个 TS 文件
            ts_urls = ts_urls[:max_ts]

            # 下载并测试每个 TS 文件的带宽
            results = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self.__test_download_speed, ts_url) for ts_url in ts_urls]
                for future in as_completed(futures):
                    try:
                        results.append(future.result())
                    except Exception as e:
                        return 0.0
            self.resolution = self.get_video_resolution(ts_url=ts_urls[0])
            return sum(results) / len(results)
        except requests.exceptions.RequestException as e:
            return 0.0
        except Exception as e:
            return 0.0

    def __test_download_speed(self, ts_url: str, m3u8_base_url: str = None) -> float:
        """
        下载并测试每个 TS 文件的带宽
        :param ts_url:
        :param m3u8_base_url:
        :return:
        """
        if not m3u8_base_url:
            m3u8_base_url = self.media_url
        # 如果 TS 文件是相对路径，则与 M3U8 URL 拼接成绝对路径
        if not ts_url.startswith('http'):
            ts_url = urljoin(m3u8_base_url, ts_url)  # 使用 urljoin 合并相对路径与基础 URL
        try:
            print(f"正在测试下载: {ts_url}")
            start_time = time.time()
            response = requests.get(ts_url, headers=HEADERS, stream=True, timeout=20)  # 设置超时时间为 20 秒
            response.raise_for_status()

            total_size = 0  # 下载数据大小（字节）
            for chunk in response.iter_content(chunk_size=8192):  # 分块下载
                total_size += len(chunk)
                if total_size >= 5 * 1024 * 1024:  # 限制最多下载 5MB 数据
                    break
                # 检查是否超过 20 秒
                if time.time() - start_time > 20:
                    raise TimeoutError("下载超时：超过 20 秒未完成")

            elapsed_time = time.time() - start_time
            speed = total_size / elapsed_time  # 下载速度 = 数据量 / 时间
            return speed
        except TimeoutError as te:
            return 0.0
        except requests.exceptions.RequestException as e:
            return 0.0
        except Exception as e:
            return 0.0

    def __test_direct_bandwidth(self) -> float:
        """
        直接测试媒体文件的带宽
        :return:
        """
        try:
            start_time = time.time()
            response = requests.get(self.media_url, headers=HEADERS, stream=True, timeout=20)  # 设置超时时间为 20 秒
            response.raise_for_status()

            total_size = 0  # 下载数据大小（字节）
            for chunk in response.iter_content(chunk_size=8192):  # 分块下载
                total_size += len(chunk)
                if total_size >= 5 * 1024 * 1024:  # 限制最多下载 5MB 数据
                    break
                # 检查是否超过 20 秒
                if time.time() - start_time > 20:
                    raise TimeoutError("下载超时：超过 20 秒未完成")

            elapsed_time = time.time() - start_time
            speed = total_size / elapsed_time  # 下载速度 = 数据量 / 时间
            self.resolution = self.get_video_resolution(ts_url=self.media_url)
            return speed
        except TimeoutError:
            return 0.0
        except requests.exceptions.RequestException:
            return 0.0
        except Exception:
            return 0.0
