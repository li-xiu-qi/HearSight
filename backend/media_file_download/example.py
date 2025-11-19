# -*- coding: utf-8 -*-
"""媒体下载工厂使用示例"""

import sys
import os
# 添加backend到路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from media_file_download.downloader_factory import MediaDownloaderFactory


def progress_callback(progress):
    """进度回调函数"""
    if progress['status'] == 'downloading':
        print(f"进度: {progress.get('_percent_str', 'N/A')}")
    elif progress['status'] == 'finished':
        print("下载完成")


def main():
    """主函数"""
    print("媒体下载工厂使用示例")

    # 创建工厂实例
    factory = MediaDownloaderFactory()

    # 示例URL（请替换为实际可用的URL）
    test_urls = [
        "https://www.bilibili.com/video/BV1arCTBSEnP",  # B站视频
        "https://www.youtube.com/watch?v=E80ZVZNiO64",  # YouTube视频
        "https://www.xiaoyuzhoufm.com/episode/6912fcf821e6d1bd34f78257",  # 小宇宙播客
    ]

    for url in test_urls:
        print(f"\n开始下载: {url}")
        result = factory.download(url, progress_callback=progress_callback)

        if result.success:
            print("下载成功！")
            print(f"标题: {result.title}")
            if result.video_path:
                print(f"视频路径: {result.video_path}")
            if result.audio_path:
                print(f"音频路径: {result.audio_path}")
        else:
            print(f"下载失败: {result.error_message}")




if __name__ == "__main__":
    main()
