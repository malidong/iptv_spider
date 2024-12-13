from iptv_spider.m3u import M3U8
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor, as_completed


# 主程序
def main(m3u_url, regex_filter: str = r'\b(cctv|CCTV)-?(?:[1-9]|1[0-7]|5\+?)\b'):
    # 下载 M3U 文件
    m = M3U8(path=m3u_url, regex_filter=regex_filter)
    best = m.get_best_channels()

    best_channels = {}

    for channel_name, channel in best.items():
        best_channels[channel_name] = {"name": channel.channel_name,
                                       "media_url": channel.media_url,
                                       "speed": channel.speed,
                                       "resolution": channel.resolution}

    # 保存结果到文件
    with open(f"./best_cctv_{datetime.today().strftime('%Y-%m-%d')}.txt", 'w',
              encoding='utf-8') as f:
        json.dump(best_channels, f, indent=4)

    # 保存结果到文件
    with open('./best_channels.m3u', 'w', encoding='utf-8') as f:
        for channel_name, best_speed_info in best_channels.items():
            if best_speed_info["speed"] > 0.3 * 1024 * 1024:
                f.write(f"{best_speed_info['meta']},{channel_name}\n"
                        f"{best_speed_info['m3u']}\n")

    print("\n最佳频道及带宽已保存到 'best_channels.m3u' 文件中")


if __name__ == "__main__":
    M3U_FILE_URL = "https://live.iptv365.org/live.m3u"
    main(M3U_FILE_URL)
