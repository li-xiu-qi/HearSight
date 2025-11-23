# -*- coding: utf-8 -*-
"""YouTube视频下载服务"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

# 添加backend到路径
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
project_root = os.path.dirname(backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config import settings

try:
    from . import youtube_login_handler
except ImportError:
    import youtube_login_handler

logger = logging.getLogger(__name__)


class YoutubeDownloader:
    """YouTube视频下载器"""

    def __init__(self, output_dir: str = None, need_login: bool = False):
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), "download_results")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.need_login = need_login
        self.cookies = youtube_login_handler.load_cookies()

        if self.need_login:
            if not self.cookies:
                logger.info("未找到保存的cookie，正在启动浏览器进行登录...")
                self.cookies = youtube_login_handler.login_and_get_cookies_sync(headless=False)
                if not self.cookies:
                    raise ValueError("登录失败，无法获取cookie")
            else:
                logger.info("已加载保存的cookie")
        else:
            if self.cookies:
                logger.info("检测到已保存的cookie，已加载并将用于下载请求")
            else:
                logger.debug("未设置登录且未找到保存的cookie，将作为匿名用户进行下载")

    def download_video(self, url: str, progress_callback: Optional[Callable[[Dict], None]] = None):
        """
        下载YouTube视频

        Args:
            url: YouTube视频URL
            progress_callback: 进度回调函数

        Returns:
            DownloadResult: 下载结果
        """
        from backend.common_interfaces import DownloadResult
        try:
            import yt_dlp

            if not self._is_youtube_url(url):
                return DownloadResult(success=False, error_message="不是有效的YouTube链接")

            with tempfile.TemporaryDirectory() as temp_dir:
                ydl_opts = {
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                    'format': 'best[ext=mp4]/best',
                    'quiet': False,
                    'no_warnings': False,
                    'socket_timeout': 30,
                    'extractor_retries': 3,
                    'skip_download': False,
                    'fixup': 'detect_or_warn',
                    'keepvideo': False,
                }

                if self.cookies:
                    try:
                        cookiefile_path = os.path.join(temp_dir, 'cookies.txt')
                        if youtube_login_handler.cookies_to_netscape(self.cookies, cookiefile_path):
                            ydl_opts['cookiefile'] = cookiefile_path
                        else:
                            cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in self.cookies])
                            ydl_opts['http_headers'] = {
                                'Cookie': cookie_str,
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                            }
                    except Exception as e:
                        logger.warning(f"设置cookiefile失败，使用header回退: {e}")
                        cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in self.cookies])
                        ydl_opts['http_headers'] = {
                            'Cookie': cookie_str,
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }

                if progress_callback:
                    ydl_opts['progress_hooks'] = [self._create_progress_hook(progress_callback)]
                if 'http_headers' not in ydl_opts:
                    ydl_opts.setdefault('http_headers', {})
                    ydl_opts['http_headers']['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info(f"开始下载YouTube视频: {url}")
                    info = ydl.extract_info(url, download=True)

                    downloaded_files = self._get_downloaded_files(temp_dir, info)

                    if not downloaded_files:
                        return DownloadResult(success=False, error_message="未找到下载的文件")

                    result = self._move_files_to_output(downloaded_files, info)

                    logger.info(f"YouTube视频下载完成: {result.title}")
                    return result

        except Exception as e:
            logger.error(f"下载YouTube视频失败: {e}", exc_info=True)
            return DownloadResult(success=False, error_message=str(e))

    def _is_youtube_url(self, url: str) -> bool:
        """检查是否为YouTube URL"""
        return 'youtube.com' in url or 'youtu.be' in url

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
                if filename.lower().endswith(('.mp4', '.webm', '.mkv', '.m4a', '.mp3', '.aac', '.wav', '.ogg')):
                    files.append(filepath)
        return files

    def _move_files_to_output(self, files: List[str], info: Dict):
        """移动文件到输出目录"""
        from backend.common_interfaces import DownloadResult
        title = info.get('title', 'unknown')
        duration = info.get('duration')

        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        if not safe_title:
            safe_title = f"youtube_video_{info.get('id', 'unknown')}"

        video_path = None
        audio_path = None

        for filepath in files:
            filename = os.path.basename(filepath)
            lower_filename = filename.lower()

            if lower_filename.endswith('.mp4'):
                target_path = self.output_dir / f"{safe_title}.mp4"
                video_path = str(target_path)
            elif lower_filename.endswith(('.m4a', '.aac', '.mp3', '.wav', '.ogg')):
                ext = Path(filepath).suffix
                target_path = self.output_dir / f"{safe_title}{ext}"
                audio_path = str(target_path)
            else:
                target_path = self.output_dir / filename

            if target_path.exists():
                target_path.unlink()

            import shutil
            shutil.move(filepath, target_path)
            logger.info(f"文件已移动: {filepath} -> {target_path}")

        if not video_path and not audio_path and files:
            first_file = files[0]
            ext = Path(first_file).suffix
            target_path = self.output_dir / f"{safe_title}{ext}"
            if video_path is None:
                video_path = str(target_path)

        if video_path and not audio_path:
            logger.info(f"检测到仅有视频无音频，使用ffmpeg进行分离: {video_path}")
            extracted_audio = self._extract_audio_with_ffmpeg(video_path, safe_title)
            if extracted_audio:
                audio_path = extracted_audio

        media_type = "both" if (video_path and audio_path) else ("video" if video_path else ("audio" if audio_path else "unknown"))

        return DownloadResult(
            video_path=video_path,
            audio_path=audio_path,
            title=title,
            duration=duration,
            media_type=media_type,
            success=True
        )

    def _extract_audio_with_ffmpeg(self, video_path: str, safe_title: str) -> Optional[str]:
        """使用ffmpeg从视频中提取音频"""
        try:
            audio_path = str(self.output_dir / f"{safe_title}.m4a")

            if os.path.exists(audio_path):
                os.remove(audio_path)

            cmd = [
                'ffmpeg',
                '-y',
                '-i', video_path,
                '-vn',
                '-acodec', 'copy',
                '-loglevel', 'error',
                audio_path
            ]
            logger.info(f"执行ffmpeg命令提取音频: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                logger.info(f"音频提取成功: {audio_path}")
                return audio_path
            else:
                logger.error(f"ffmpeg提取音频失败: {result.stderr}")
                return None
        except FileNotFoundError:
            logger.error("ffmpeg未安装或未在PATH中")
            return None
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg提取音频超时")
            return None
        except Exception as e:
            logger.error(f"ffmpeg提取音频异常: {e}")
            return None


_downloader = None

def get_downloader(need_login: bool = False) -> YoutubeDownloader:
    """获取下载器实例"""
    global _downloader
    if _downloader is None or _downloader.need_login != need_login:
        _downloader = YoutubeDownloader(need_login=need_login)
    return _downloader

def download_youtube_video(url: str, progress_callback: Optional[Callable[[Dict], None]] = None, need_login: bool = False):
    """
    下载YouTube视频的便捷函数

    Args:
        url: YouTube视频URL
        progress_callback: 进度回调函数

    Returns:
        DownloadResult: 下载结果
    """
    from backend.common_interfaces import DownloadResult
    downloader = get_downloader(need_login=need_login)
    return downloader.download_video(url, progress_callback)
