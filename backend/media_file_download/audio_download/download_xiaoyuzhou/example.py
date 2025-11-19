# -*- coding: utf-8 -*-
"""小宇宙播客下载测试"""

import asyncio
from xiaoyuzhou_downloader import download_xiaoyuzhou_episode


def test_download():
    """测试下载功能"""
    # 测试URL
    test_url = "https://www.xiaoyuzhoufm.com/episode/6912fcf821e6d1bd34f78257?s=eyJ1IjogIjY2MTU0MjQ1ZWRjZTY3MTA0YTFiNTUxMiJ9"

    def progress_callback(progress):
        print(f"进度: {progress['status']} - {progress['progress_percent']:.1f}%")

    print("开始测试下载...")
    result = download_xiaoyuzhou_episode(test_url, progress_callback)

    if result.success:
        print("下载成功！")
        print(f"标题: {result.title}")
        print(f"媒体类型: {result.media_type}")
        print(f"音频路径: {result.audio_path}")
        print(f"时长: {result.duration}秒")
    else:
        print(f"下载失败: {result.error_message}")


if __name__ == "__main__":
    test_download()