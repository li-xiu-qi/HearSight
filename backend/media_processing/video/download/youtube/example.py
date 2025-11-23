"""
YouTube视频下载示例脚本
使用youtube_downloader模块下载指定的YouTube视频
"""

import os
import sys

# 添加backend到路径，确保绝对导入正常工作
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
project_root = os.path.dirname(backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from backend.media_processing.video.download.youtube.youtube_downloader import download_youtube_video
except ImportError:
    try:
        from .youtube_downloader import download_youtube_video
    except ImportError:
        raise ImportError("无法导入必要的模块，请检查项目结构")

def progress_callback(progress_info):
    """
    进度回调函数
    """
    status = progress_info.get('status', 'unknown')
    progress_percent = progress_info.get('progress_percent', 0)
    print(f"下载状态: {status}, 进度: {progress_percent:.2f}%")

if __name__ == "__main__":
    # 测试URL
    test_url = "https://www.youtube.com/watch?v=A6ZgS0vGsl8"

    print("开始下载YouTube视频...")
    result = download_youtube_video(test_url, progress_callback=progress_callback)

    if result.success:
        print("下载成功!")
        print(f"标题: {result.title}")
        print(f"视频路径: {result.video_path}")
        print(f"音频路径: {result.audio_path}")
        print(f"时长: {result.duration}秒")
        print(f"媒体类型: {result.media_type}")
    else:
        print(f"下载失败: {result.error_message}")
