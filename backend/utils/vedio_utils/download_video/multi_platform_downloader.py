# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
from typing import Callable, Dict, List, Optional

from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)


class MultiPlatformDownloader:
    """
    多平台媒体下载器，使用 yt-dlp 库支持多种视频和音频平台的下载。

    支持的平台包括：
    - B站 (bilibili.com, b23.tv)
    - YouTube (youtube.com, youtu.be)
    - 小宇宙播客 (xiaoyuzhoufm.com)

    主要功能：
    - 自动检测URL平台
    - 下载视频或音频文件
    - 支持进度回调
    - 处理播放列表
    - 合并音视频（除小宇宙外）
    """

    def __init__(
        self,
        url: str,
        out_dir: str = "downloads",
        progress_callback: Optional[Callable[[Dict], None]] = None,
        **kwargs,
    ):
        """
        初始化下载器。

        Args:
            url: 要下载的媒体URL
            out_dir: 输出目录，默认为'downloads'
            progress_callback: 进度回调函数，接收进度信息字典
            **kwargs: 其他可选参数（目前未使用）
        """
        self.url = url
        self.out_dir = out_dir
        self.progress_callback = progress_callback
        self.platform = self._detect_platform(url)

    def _detect_platform(self, url: str) -> str:
        """
        根据URL检测媒体平台。

        通过检查URL中是否包含特定域名来识别平台。
        如果不匹配任何已知平台，返回'default'。

        Args:
            url: 要检测的URL

        Returns:
            平台名称字符串：'bilibili', 'youtube', 'xiaoyuzhou', 或 'default'
        """
        if "bilibili.com" in url or "b23.tv" in url:
            return "bilibili"
        if "youtube.com" in url or "youtu.be" in url:
            return "youtube"
        if "xiaoyuzhoufm.com" in url:
            return "xiaoyuzhou"
        return "default"

    def download(self) -> List[str]:
        """
        执行媒体下载并返回下载的文件路径列表。

        使用 yt-dlp 进行下载，支持单个视频或播放列表。
        下载过程中会记录日志，并在出错时抛出异常。

        Returns:
            下载成功的文件路径列表

        Raises:
            Exception: 下载过程中发生的任何异常
        """
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
        """
        构建 yt-dlp 的配置选项字典。

        根据平台设置不同的选项：
        - 小宇宙播客为纯音频，不进行音视频合并
        - 其他平台合并为MP4格式

        包含下载重试、格式选择、输出模板等配置。

        Returns:
            yt-dlp 选项字典
        """
        # 小宇宙是纯音频，不需要合并
        merge_format = "mp4" if self.platform != "xiaoyuzhou" else None

        opts = {
            "outtmpl": os.path.join(self.out_dir, "%(title)s.%(ext)s"),  # 输出文件模板
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",  # 格式选择
            "keepvideo": False,  # 下载后不保留中间文件
            "quiet": False,  # 不静默模式
            "windowsfilenames": True,  # Windows兼容文件名
            "nopart": os.name == "nt",  # Windows下不使用.part文件
            "retries": 3,  # 下载重试次数
            "fragment_retries": 3,  # 分片重试次数
            "skip_unavailable_fragments": True,  # 跳过不可用分片
            "continuedl": False,  # 不继续下载（每次重新开始）
        }

        if merge_format:
            opts["merge_output_format"] = merge_format

        if self.progress_callback:
            opts["progress_hooks"] = [self._progress_hook]
        return opts

    def _progress_hook(self, d: Dict) -> None:
        """
        yt-dlp 进度回调钩子函数。

        将 yt-dlp 的进度信息转换为标准格式并调用用户提供的回调函数。
        进度信息包括下载状态、百分比、字节数、速度、预计时间等。

        Args:
            d: yt-dlp 提供的进度字典
        """
        if self.progress_callback:
            status = d.get("status", "unknown")
            progress_info = {
                "status": status,  # 下载状态：downloading, finished等
                "progress_percent": (  # 下载进度百分比
                    d.get("downloaded_bytes", 0) / d.get("total_bytes", 1) * 100
                    if d.get("total_bytes")
                    else 0
                ),
                "downloaded_bytes": d.get("downloaded_bytes", 0),  # 已下载字节数
                "total_bytes": d.get("total_bytes", 0),  # 总字节数
                "speed": d.get("speed", 0),  # 下载速度（字节/秒）
                "eta_seconds": d.get("eta"),  # 预计剩余时间（秒）
                "filename": os.path.basename(d.get("filename", "")),  # 文件名
                "timestamp": "",  # 时间戳（目前为空）
            }
            self.progress_callback(progress_info)

    @staticmethod
    def _extract_file_paths(ydl: YoutubeDL, info: dict) -> List[str]:
        """
        从 yt-dlp 的信息字典中提取实际下载的文件路径。

        处理播放列表和单个视频的情况。
        优先检查合并后的文件（如果配置了合并格式），
        否则使用原始下载的文件。

        Args:
            ydl: YoutubeDL 实例
            info: yt-dlp 提取的信息字典

        Returns:
            文件路径列表
        """
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
        """
        检查是否支持下载给定的URL。

        通过检查URL是否包含已知平台的域名来判断支持性。
        支持的平台包括B站、YouTube、小宇宙播客。

        Args:
            url: 要检查的URL

        Returns:
            如果支持该URL返回True，否则False
        """
        platforms = [
            "bilibili.com",
            "b23.tv",
            "youtube.com",
            "youtu.be",
            "xiaoyuzhoufm.com",
        ]
        return any(platform in url for platform in platforms)
