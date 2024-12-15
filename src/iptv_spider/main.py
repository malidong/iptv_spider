from argparse import Namespace

from src.iptv_spider.m3u import M3U8
from datetime import datetime
import json
import argparse


def arg_parser() -> Namespace:
    parser = argparse.ArgumentParser(description="解析输入参数")

    # 添加参数：url_or_path（可选，string 类型）
    parser.add_argument(
        "--url_or_path",
        type=str,
        default="https://live.iptv365.org/live.m3u",
        help="URL 或文件路径，默认为 https://live.iptv365.org/live.m3u"
    )

    # 添加参数：filter（可选，string 类型）
    parser.add_argument(
        "--filter",
        type=str,
        default=r'\b(cctv|CCTV)-?(?:[1-9]|1[0-7]|5\+?)\b',
        help="正则匹配，默认匹配CCTV频道"
    )

    # 解析命令行参数
    params = parser.parse_args()
    return params


# 主程序
def main(m3u_url, regex_filter: str):
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
    args = arg_parser()
    main(m3u_url=args.url_or_path,
         regex_filter=args.filter)
