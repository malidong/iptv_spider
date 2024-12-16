# -*- coding: utf-8 -*-
"""
# This is the entry module for iptv_spider.
"""
from argparse import Namespace
from datetime import datetime
import json
import argparse
from iptv_spider.m3u import M3U8


def arg_parser() -> Namespace:
    """
    从参数读取下载地址和匹配模式，可以为空。
    :return:
    """
    parser = argparse.ArgumentParser(description="从参数读取下载地址(url_or_path)和匹配模式(filter)，可以为空。")

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
    """
    URL或者本地的path读取iptv的列表，根据regex_filter对频道名进行过滤，获取过滤后同名频道中速度最好的url。
    :param m3u_url: 需要下载的m3u8地址，支持本地地址。
    :param regex_filter: 频道名匹配用正则表达式。
    :return:
    """
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
