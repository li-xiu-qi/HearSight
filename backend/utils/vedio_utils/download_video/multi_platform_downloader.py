# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import logging
from typing import Optional, Callable, List, Dict
from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)


class MultiPlatformDownloader:
    """多平台媒体下载器，支持B站、YouTube、小宇宙播客等"""

    def __init__(
        self,
        url: str,
        out_dir: str = "downloads",
        progress_callback: Optional[Callable[[Dict], None]] = None,
        **kwargs,
    ):
        self.url = url
        self.out_dir = out_dir
        self.progress_callback = progress_callback
        self.platform = self._detect_platform(url)

    def _detect_platform(self, url: str) -> str:
        """检测URL对应的平台"""
        if "bilibili.com" in url or "b23.tv" in url:
            return "bilibili"
        if "youtube.com" in url or "youtu.be" in url:
            return "youtube"
        if "xiaoyuzhoufm.com" in url:
            return "xiaoyuzhou"
        return "default"

    def download(self) -> List[str]:
        """执行下载并返回文件路径列表"""
        ydl_opts = self._build_ydl_options()

        results: List[str] = []
        try:
            with YoutubeDL(ydl_opts) as ydl:
                logger.info(f"开始下载 {self.platform} 媒体: {self.url}")
                info = ydl.extract_info(self.url, download=True)
                results = self._extract_file_paths(ydl, info)
                logger.info(f"下载完成，共获得 {len(results)} 个文件: {results}")
        except Exception as e:
            logger.error(f"下载过程中发生错误: {str(e)}")
            raise e

        return results

    def _build_ydl_options(self) -> dict:
        """构建 yt-dlp 选项"""
        # 小宇宙是纯音频，不需要合并
        merge_format = "mp4" if self.platform != "xiaoyuzhou" else None

        opts = {
            "outtmpl": os.path.join(self.out_dir, "%(title)s.%(ext)s"),
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "keepvideo": False,
            "quiet": False,
            "windowsfilenames": True,
            "nopart": os.name == "nt",
            "retries": 3,
            "fragment_retries": 3,
            "skip_unavailable_fragments": True,
            "continuedl": False,
        }

        if merge_format:
            opts["merge_output_format"] = merge_format

        if self.progress_callback:
            opts["progress_hooks"] = [self._progress_hook]
        return opts

    def _progress_hook(self, d: Dict) -> None:
        """yt-dlp 进度钩子"""
        if self.progress_callback:
            status = d.get("status", "unknown")
            progress_info = {
                "status": status,
                "progress_percent": (
                    d.get("downloaded_bytes", 0) / d.get("total_bytes", 1) * 100
                    if d.get("total_bytes")
                    else 0
                ),
                "downloaded_bytes": d.get("downloaded_bytes", 0),
                "total_bytes": d.get("total_bytes", 0),
                "speed": d.get("speed", 0),
                "eta_seconds": d.get("eta"),
                "filename": os.path.basename(d.get("filename", "")),
                "timestamp": "",
            }
            self.progress_callback(progress_info)

    @staticmethod
    def _extract_file_paths(ydl: YoutubeDL, info: dict) -> List[str]:
        """提取文件路径列表"""
        results: List[str] = []
        if not info:
            return results

        # 处理播放列表情况
        if "entries" in info:
            for entry in info["entries"]:
                results.extend(MultiPlatformDownloader._extract_file_paths(ydl, entry))
        else:
            try:
                filename = ydl.prepare_filename(info)
                merge_fmt = ydl.params.get("merge_output_format")

                # 如果配置了输出格式，尝试这个格式的文件
                if merge_fmt:
                    base, _ = os.path.splitext(filename)
                    merged_filename = f"{base}.{merge_fmt}"
                    if os.path.exists(merged_filename):
                        results.append(merged_filename)
                        return results

                # 否则使用原始文件名（可能是纯音频如m4a）
                if os.path.exists(filename):
                    results.append(filename)
            except Exception as e:
                logger.warning(f"提取文件路径失败: {e}")

        return results

    @classmethod
    def supports_url(cls, url: str) -> bool:
        """检查是否支持该URL"""
        platforms = [
            "bilibili.com",
            "b23.tv",
            "youtube.com",
            "youtu.be",
            "xiaoyuzhoufm.com",
        ]
        return any(platform in url for platform in platforms)
