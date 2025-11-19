# -*- coding: utf-8 -*-
"""b站视频下载测试"""

import asyncio
from bilibili_downloader import download_bilibili_video


def test_download():
    """测试下载功能"""
    # 测试URL
    test_url = "https://www.bilibili.com/video/BV1arCTBSEnP/?spm_id_from=333.1007.tianma.4-3-13.click"  # 示例URL，请替换

    def progress_callback(progress):
        print(f"进度: {progress['status']} - {progress['progress_percent']:.1f}%")

    print("开始测试下载...")
    result = download_bilibili_video(test_url, progress_callback)

    if result.success:
        print("下载成功！")
        print(f"标题: {result.title}")
        print(f"视频路径: {result.video_path}")
        print(f"音频路径: {result.audio_path}")
        print(f"时长: {result.duration}秒")
    else:
        print(f"下载失败: {result.error_message}")


if __name__ == "__main__":
    test_download()