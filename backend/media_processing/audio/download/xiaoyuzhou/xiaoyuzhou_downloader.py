# -*- coding: utf-8 -*-
"""小宇宙播客下载服务"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

# 添加backend到路径
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config import settings

from backend.common_interfaces import DownloadResult

logger = logging.getLogger(__name__)


class XiaoyuzhouDownloader:
    """小宇宙播客下载器"""

    def __init__(self, output_dir: str = None):
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), "download_results")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_episode(self, url: str, progress_callback: Optional[Callable[[Dict], None]] = None) -> DownloadResult:
        """
        下载小宇宙播客

        Args:
            url: 小宇宙播客URL
            progress_callback: 进度回调函数

        Returns:
            DownloadResult: 下载结果
        """
        try:
            import yt_dlp

            # 检查URL是否为小宇宙链接
            if not self._is_xiaoyuzhou_url(url):
                return DownloadResult(success=False, error_message="不是有效的小宇宙链接")

            # 创建临时下载目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # yt-dlp配置 - 下载音频
                ydl_opts = {
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                    'format': 'bestaudio/best',  # 下载最佳音频
                    'extractaudio': True,
                    'audioformat': 'mp3',  # 转换为MP3
                    'keepvideo': False,  # 不保留视频
                    'quiet': False,
                    'no_warnings': False,
                }

                if progress_callback:
                    ydl_opts['progress_hooks'] = [self._create_progress_hook(progress_callback)]

                # 下载播客
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info(f"开始下载小宇宙播客: {url}")
                    info = ydl.extract_info(url, download=True)

                    # 获取下载的文件
                    downloaded_files = self._get_downloaded_files(temp_dir, info)

                    if not downloaded_files:
                        return DownloadResult(success=False, error_message="未找到下载的文件")

                    # 移动文件到输出目录
                    result = self._move_files_to_output(downloaded_files, info)

                    logger.info(f"小宇宙播客下载完成: {result.title}")
                    return result

        except Exception as e:
            logger.error(f"下载小宇宙播客失败: {e}", exc_info=True)
            return DownloadResult(success=False, error_message=str(e))

    def _is_xiaoyuzhou_url(self, url: str) -> bool:
        """检查是否为小宇宙 URL"""
        return 'xiaoyuzhoufm.com' in url

    def _get_audio_duration(self, file_path: str) -> Optional[float]:
        """获取音频文件时长"""
        try:
            import subprocess
            import json
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', file_path],
                capture_output=True, text=True, encoding='utf-8', check=True
            )
            if result.stdout:
                data = json.loads(result.stdout)
                return float(data['format']['duration'])
            else:
                return None
        except Exception as e:
            logger.warning(f"获取音频时长失败: {e}")
            return None

    def _create_progress_hook(self, callback: Callable[[Dict], None]):
        """创建进度回调钩子"""
        def progress_hook(d):
            if callback:
                status = d.get('status', 'unknown')
                total_bytes = d.get('total_bytes', 0)
                downloaded_bytes = d.get('downloaded_bytes', 0)

                progress_percent = 0
                if total_bytes > 0:
                    progress_percent = (downloaded_bytes / total_bytes) * 100

                progress_info = {
                    'status': status,
                    'progress_percent': progress_percent,
                    'downloaded_bytes': downloaded_bytes,
                    'total_bytes': total_bytes,
                    'speed': d.get('speed', 0),
                    'eta_seconds': d.get('eta', 0),
                    'filename': os.path.basename(d.get('filename', ''))
                }
                callback(progress_info)

        return progress_hook

    def _get_downloaded_files(self, temp_dir: str, info: Dict) -> List[str]:
        """获取下载的文件列表"""
        files = []
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)
            if os.path.isfile(filepath):
                files.append(filepath)
        return files

    def _move_files_to_output(self, files: List[str], info: Dict) -> DownloadResult:
        """移动文件到输出目录"""
        title = info.get('title', 'unknown')
        duration = info.get('duration')

        # 清理标题作为文件名
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        if not safe_title:
            safe_title = f"xiaoyuzhou_episode_{info.get('id', 'unknown')}"

        audio_path = None

        for filepath in files:
            filename = os.path.basename(filepath)
            lower_filename = filename.lower()

            # 确定目标路径
            if lower_filename.endswith(('.mp3', '.m4a', '.aac')):
                target_path = self.output_dir / f"{safe_title}.{lower_filename.split('.')[-1]}"
                audio_path = str(target_path)
            else:
                # 其他格式也移动
                target_path = self.output_dir / filename

            # 移动文件
            if target_path.exists():
                target_path.unlink()  # 删除已存在的文件

            import shutil
            shutil.move(filepath, target_path)
            logger.info(f"文件已移动: {filepath} -> {target_path}")

        # 如果yt-dlp未获取到时长，尝试从文件获取
        if duration is None and audio_path:
            duration = self._get_audio_duration(audio_path)

        return DownloadResult(
            audio_path=audio_path,
            title=title,
            duration=duration,
            media_type="audio",
            success=True
        )


# 全局下载器实例
_downloader = None

def get_downloader() -> XiaoyuzhouDownloader:
    """获取下载器实例"""
    global _downloader
    if _downloader is None:
        _downloader = XiaoyuzhouDownloader()
    return _downloader

def download_xiaoyuzhou_episode(url: str, progress_callback: Optional[Callable[[Dict], None]] = None) -> DownloadResult:
    """
    下载小宇宙播客的便捷函数

    Args:
        url: 小宇宙播客URL
        progress_callback: 进度回调函数

    Returns:
        DownloadResult: 下载结果
    """
    downloader = get_downloader()
    return downloader.download_episode(url, progress_callback)
