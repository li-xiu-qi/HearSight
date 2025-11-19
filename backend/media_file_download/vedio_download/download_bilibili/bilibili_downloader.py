# -*- coding: utf-8 -*-
"""b站视频下载服务"""

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
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# backend_dir 指向 .../HearSight/backend
project_root = os.path.dirname(backend_dir)
# 把项目根和 backend 两个路径都加入 sys.path，以兼容不同的导入样式
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config import settings

from media_file_download.common_interfaces import DownloadResult

# 智能导入 bilibili_login_handler
try:
    # 尝试相对导入（在包内运行时）
    from . import bilibili_login_handler
except ImportError:
    # 回退到直接导入（直接运行时）
    import bilibili_login_handler

logger = logging.getLogger(__name__)


class BilibiliDownloader:
    """b站视频下载器"""

    def __init__(self, output_dir: str = None, need_login: bool = False):
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), "download_results")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.need_login = need_login
        self.cookies = bilibili_login_handler.load_cookies()

        # 如果设置need_login为True且未找到cookie，则强制登录获取cookie
        if self.need_login:
            if not self.cookies:
                logger.info("未找到保存的cookie，正在启动浏览器进行登录...")
                self.cookies = bilibili_login_handler.login_and_get_cookies_sync(headless=False)
                if not self.cookies:
                    raise ValueError("登录失败，无法获取cookie")
            else:
                logger.info("已加载保存的cookie")
        else:
            if self.cookies:
                logger.info("检测到已保存的cookie，已加载并将用于下载请求")
            else:
                logger.debug("未设置登录且未找到保存的cookie，将作为匿名用户进行下载")

    def download_video(self, url: str, progress_callback: Optional[Callable[[Dict], None]] = None) -> DownloadResult:
        """
        下载b站视频

        Args:
            url: b站视频URL
            progress_callback: 进度回调函数

        Returns:
            DownloadResult: 下载结果
        """
        try:
            import yt_dlp

            # 检查URL是否为b站链接
            if not self._is_bilibili_url(url):
                return DownloadResult(success=False, error_message="不是有效的b站链接")

            # 创建临时下载目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # yt-dlp配置 - 下载分离的视频和音频流，不自动合并
                ydl_opts = {
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                    'format': 'bestvideo[ext=mp4],bestaudio[ext=m4a]/best[ext=mp4]/best',  # 分离下载，不合并
                    'keepvideo': True,  # 保留视频文件
                    'quiet': False,
                    'no_warnings': False,
                }

                # 优先使用 cookiefile（Netscape 格式），若未能导出则退回到 header 模式
                if self.cookies:
                    try:
                        cookiefile_path = os.path.join(temp_dir, 'cookies.txt')
                        if bilibili_login_handler.cookies_to_netscape(self.cookies, cookiefile_path):
                            ydl_opts['cookiefile'] = cookiefile_path
                        else:
                            # 回退到 header 方式（兼容旧逻辑）
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
                # 默认User-Agent，如果未通过http_headers设置，仍可以在 ydl_opts 中设置 'user_agent'
                if 'http_headers' not in ydl_opts:
                    ydl_opts.setdefault('http_headers', {})
                    ydl_opts['http_headers']['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

                # 下载视频
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info(f"开始下载b站视频: {url}")
                    info = ydl.extract_info(url, download=True)

                    # 获取下载的文件
                    downloaded_files = self._get_downloaded_files(temp_dir, info)

                    if not downloaded_files:
                        return DownloadResult(success=False, error_message="未找到下载的文件")

                    # 移动文件到输出目录
                    result = self._move_files_to_output(downloaded_files, info)

                    logger.info(f"b站视频下载完成: {result.title}")
                    return result

        except Exception as e:
            logger.error(f"下载b站视频失败: {e}", exc_info=True)
            return DownloadResult(success=False, error_message=str(e))

    def _is_bilibili_url(self, url: str) -> bool:
        """检查是否为b站URL"""
        return 'bilibili.com' in url or 'b23.tv' in url

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
                # 只包含媒体文件
                if filename.lower().endswith(('.mp4', '.webm', '.mkv', '.m4a', '.mp3', '.aac', '.wav', '.ogg')):
                    files.append(filepath)
        return files

    def _move_files_to_output(self, files: List[str], info: Dict) -> DownloadResult:
        """移动文件到输出目录并合并音视频"""
        title = info.get('title', 'unknown')
        duration = info.get('duration')

        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        if not safe_title:
            safe_title = f"bilibili_video_{info.get('id', 'unknown')}"

        video_path = None
        audio_path = None
        temp_video_path = None

        for filepath in files:
            filename = os.path.basename(filepath)
            lower_filename = filename.lower()

            if lower_filename.endswith('.mp4'):
                temp_video_path = filepath
                # 复制视频到输出目录
                target_video_path = self.output_dir / f"{safe_title}.mp4"
                if target_video_path.exists():
                    target_video_path.unlink()
                import shutil
                shutil.copy(filepath, target_video_path)
                video_path = str(target_video_path)
            elif lower_filename.endswith('.m4a'):
                target_audio_path = self.output_dir / f"{safe_title}.m4a"
                if target_audio_path.exists():
                    target_audio_path.unlink()
                import shutil
                shutil.move(filepath, target_audio_path)
                audio_path = str(target_audio_path)
                logger.info(f"音频文件已保存: {audio_path}")
            else:
                target_path = self.output_dir / filename
                if target_path.exists():
                    target_path.unlink()
                import shutil
                shutil.move(filepath, target_path)

        if temp_video_path and audio_path:
            # 合并音视频到临时文件，然后替换原文件
            temp_merged_path = video_path.replace('.mp4', '_merged.mp4')
            merged_video_path = self._merge_audio_video(video_path, audio_path, temp_merged_path)
            if merged_video_path:
                # 删除原视频文件，将临时文件重命名为最终文件
                if os.path.exists(video_path):
                    os.remove(video_path)
                import shutil
                shutil.move(temp_merged_path, video_path)
                logger.info(f"音视频合并成功: {video_path}")
            else:
                logger.warning("音视频合并失败，使用纯视频文件")
                if os.path.exists(temp_merged_path):
                    os.remove(temp_merged_path)
        elif temp_video_path:
            logger.info(f"视频文件已保存: {video_path}")

        media_type = "both" if (video_path and audio_path) else ("video" if video_path else ("audio" if audio_path else "unknown"))

        return DownloadResult(
            video_path=video_path,
            audio_path=audio_path,
            title=title,
            duration=duration,
            media_type=media_type,
            success=True
        )

    def _merge_audio_video(self, video_path: str, audio_path: str, output_path: str) -> Optional[str]:
        """使用ffmpeg合并音频和视频"""
        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-y',
                output_path
            ]
            print(f"开始合并音视频...")
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=600)
            if result.returncode == 0:
                print(f"音视频合并成功: {output_path}")
                return output_path
            else:
                print(f"ffmpeg合并音视频失败，返回码: {result.returncode}")
                print(f"stderr: {result.stderr}")
                return None
        except FileNotFoundError:
            print("ffmpeg未安装或未在PATH中")
            return None
        except subprocess.TimeoutExpired:
            print("ffmpeg合并音视频超时")
            return None
        except Exception as e:
            print(f"ffmpeg合并音视频异常: {e}")
            return None

    def _parse_time(self, time_str: str) -> float:
        """解析时间字符串为秒数"""
        try:
            h, m, s = time_str.split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
        except:
            return 0


# 全局下载器实例
_downloader = None

def get_downloader(need_login: bool = False) -> BilibiliDownloader:
    """获取下载器实例"""
    global _downloader
    if _downloader is None or _downloader.need_login != need_login:
        _downloader = BilibiliDownloader(need_login=need_login)
    return _downloader

def download_bilibili_video(url: str, progress_callback: Optional[Callable[[Dict], None]] = None, need_login: bool = False) -> DownloadResult:
    """
    下载b站视频的便捷函数

    Args:
        url: b站视频URL
        progress_callback: 进度回调函数
        need_login: 是否需要登录

    Returns:
        DownloadResult: 下载结果
    """
    downloader = get_downloader(need_login=need_login)
    return downloader.download_video(url, progress_callback)