# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import glob
import json
from yt_dlp import YoutubeDL
import logging
from typing import Optional, Callable, TypedDict
from datetime import datetime

logger = logging.getLogger(__name__)


class ProgressInfo(TypedDict):
    """进度信息类型"""
    status: str
    progress_percent: float
    downloaded_bytes: int
    total_bytes: int
    speed: float
    eta_seconds: Optional[int]
    filename: str
    timestamp: str


class DownloadProgressTracker:
    """下载进度追踪器"""

    def __init__(self, progress_callback: Optional[Callable[[ProgressInfo], None]] = None):
        """
        初始化进度追踪器。

        Args:
            progress_callback: 进度更新回调函数，接收 ProgressInfo 字典
        """
        self.progress_callback = progress_callback
        self.last_callback_time = 0
        self.callback_interval = 0.5  # 最多每0.5秒回调一次，避免过于频繁

    def _format_bytes(self, bytes_value: int) -> str:
        """格式化字节数为可读格式"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.2f} TB"

    def _format_time(self, seconds: Optional[int]) -> str:
        """格式化秒数为可读格式"""
        if seconds is None:
            return "N/A"
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            return f"{seconds // 3600}h {(seconds % 3600) // 60}m"

    def _make_progress_info(self, status: str, d: dict) -> ProgressInfo:
        """构建进度信息"""
        filename = d.get("filename", "unknown")
        basename = os.path.basename(filename) if filename else "unknown"

        if status == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes", 0)
            progress_percent = (downloaded / total * 100) if total > 0 else 0
            return {
                "status": "downloading",
                "progress_percent": round(progress_percent, 1),
                "downloaded_bytes": downloaded,
                "total_bytes": total,
                "speed": d.get("speed") or 0,
                "eta_seconds": d.get("eta"),
                "filename": basename,
                "timestamp": datetime.now().isoformat(),
            }
        elif status == "finished":
            return {
                "status": "finished",
                "progress_percent": 100.0,
                "downloaded_bytes": d.get("downloaded_bytes", 0),
                "total_bytes": d.get("total_bytes", 0),
                "speed": 0,
                "eta_seconds": None,
                "filename": basename,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            return {
                "status": "error",
                "progress_percent": 0,
                "downloaded_bytes": 0,
                "total_bytes": 0,
                "speed": 0,
                "eta_seconds": None,
                "filename": basename,
                "timestamp": datetime.now().isoformat(),
            }

    def progress_hook(self, d: dict) -> None:
        """yt-dlp 的进度钩子函数"""
        import time
        status = d.get("status", "unknown")

        if status == "downloading":
            current_time = time.time()
            if current_time - self.last_callback_time >= self.callback_interval:
                progress_info = self._make_progress_info(status, d)
                self._invoke_callback(progress_info)
                self.last_callback_time = current_time
        else:
            progress_info = self._make_progress_info(status, d)
            self._invoke_callback(progress_info)

    def _invoke_callback(self, progress_info: ProgressInfo) -> None:
        """调用进度回调"""
        if self.progress_callback:
            try:
                self.progress_callback(progress_info)
            except Exception as e:
                logger.error(f"进度回调执行出错: {e}")


def _clean_temp_files(out_dir: str, title: str):
    """清理可能存在的临时文件"""
    try:
        temp_patterns = [
            os.path.join(out_dir, f"{title}.*.part"),
            os.path.join(out_dir, f"{title}.*.tmp"),
            os.path.join(out_dir, f"{title}.*.part-Frag*"),
            os.path.join(out_dir, f"{title}.*.temp.*"),
        ]

        for pattern in temp_patterns:
            for temp_file in glob.glob(pattern):
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.info(f"已清理临时文件: {temp_file}")
    except Exception as e:
        logger.warning(f"清理临时文件时出错: {e}")


def _build_ydl_options(
    quality: str,
    out_dir: str,
    simple_filename: bool,
    workers: int,
    use_nopart: bool,
    http_headers: dict | None,
    tracker: DownloadProgressTracker,
) -> dict:
    """构建 yt-dlp 选项"""
    fmt = "bv*+ba/best" if quality == "best" else quality
    outtmpl = os.path.join(out_dir, "%(title)s.%(ext)s") if simple_filename else os.path.join(out_dir, "%(title)s [%(id)s][P%(playlist_index)02d].%(ext)s")

    opts = {
        "format": fmt,
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
        "quiet": False,
        "overwrites": True,
        "windowsfilenames": True,
        "retries": 3,
        "fragment_retries": 3,
        "skip_unavailable_fragments": True,
        "continuedl": True,
        "noresizebuffer": True,
        "file_access_retries": 3,
        "socket_timeout": 30,
        "sleep_interval": 1,
        "max_sleep_interval": 5,
        "progress_hooks": [tracker.progress_hook],
        "concurrent_fragment_downloads": workers,
    }

    if http_headers:
        opts["http_headers"] = http_headers
    if use_nopart:
        opts["nopart"] = True

    return opts


def _extract_single_filepath(ydl: YoutubeDL, item: dict) -> str | None:
    """从 item 中提取单个文件路径"""
    fp = item.get("filepath") if isinstance(item, dict) else None
    if not fp:
        try:
            guessed = ydl.prepare_filename(item)
            merge_fmt = ydl.params.get("merge_output_format")
            if merge_fmt:
                base, _ = os.path.splitext(guessed)
                guessed = f"{base}.{merge_fmt}"
            fp = guessed
        except Exception:
            fp = None
    return fp


def _iter_entries(info):
    """递归遍历 entries"""
    if not info:
        return
    entries = info.get("entries") if isinstance(info, dict) else None
    if entries:
        for e in entries:
            yield from _iter_entries(e)
    else:
        yield info


def _extract_file_paths(ydl: YoutubeDL, info: dict) -> list[str]:
    """提取文件路径列表"""
    results: list[str] = []
    for item in _iter_entries(info):
        fp = _extract_single_filepath(ydl, item)
        if fp:
            results.append(fp)
    return results


def download_bilibili_with_progress(
    url: str,
    out_dir: str = "downloads",
    progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    sessdata: Optional[str] = None,
    playlist: bool = False,
    quality: str = "best",
    workers: int = 1,
    use_nopart: bool | None = None,
    simple_filename: bool = True,
) -> list[str]:
    """支持进度回调的 Bilibili 下载函数"""
    os.makedirs(out_dir, exist_ok=True)

    if use_nopart is None:
        use_nopart = os.name == "nt"

    http_headers = {"Cookie": f"SESSDATA={sessdata}"} if sessdata else None
    tracker = DownloadProgressTracker(progress_callback)

    ydl_opts = _build_ydl_options(
        quality,
        out_dir,
        simple_filename,
        workers,
        use_nopart,
        http_headers,
        tracker,
    )
    ydl_opts["noplaylist"] = not playlist

    results: list[str] = []
    try:
        with YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(url, download=False)
                title = info_dict.get("title", "unknown") if isinstance(info_dict, dict) else "unknown"
                _clean_temp_files(out_dir, title)
            except Exception as e:
                logger.warning(f"获取视频信息时出错: {e}")

            info = ydl.extract_info(url, download=True)
            results = _extract_file_paths(ydl, info)
    except Exception as e:
        logger.error(f"下载过程中发生错误: {str(e)}")
        raise e

    return results
