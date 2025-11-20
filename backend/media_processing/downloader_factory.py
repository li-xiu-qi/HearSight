# -*- coding: utf-8 -*-
"""媒体下载工厂模式实现"""

from __future__ import annotations

import logging
import re
import sys
import os
from typing import Optional, Callable, Dict
from abc import ABC, abstractmethod

# 添加backend到路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from .common_interfaces import DownloadResult
from .audio.download.xiaoyuzhou.xiaoyuzhou_downloader import XiaoyuzhouDownloader
from .video.download.bilibili.bilibili_downloader import BilibiliDownloader
from .video.download.youtube.youtube_downloader import YoutubeDownloader

logger = logging.getLogger(__name__)


class MediaDownloaderBase(ABC):
    """媒体下载器基类"""

    @abstractmethod
    def download(self, url: str, progress_callback: Optional[Callable[[Dict], None]] = None) -> DownloadResult:
        """下载媒体"""
        pass


class MediaDownloaderFactory:
    """媒体下载器工厂类

    支持自动识别媒体源并返回对应的下载器实例，提供统一的下载接口。
    """

    # 支持的媒体源正则表达式映射
    _SOURCE_PATTERNS = {
        'bilibili': r'(?:https?://)?(?:www\.)?bilibili\.com',
        'youtube': r'(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)',
        'xiaoyuzhou': r'(?:https?://)?(?:www\.)?xiaoyuzhoufm\.com',
    }

    def __init__(self, output_dir: Optional[str] = None, need_login: bool = False):
        """
        初始化下载工厂

        Args:
            output_dir: 下载输出目录
            need_login: 是否需要登录
        """
        self.output_dir = output_dir
        self.need_login = need_login
        self._downloaders_cache: Dict[str, object] = {}

    def _get_source_type(self, url: str) -> Optional[str]:
        """
        根据URL识别媒体源类型

        Args:
            url: 媒体URL

        Returns:
            源类型标识符，若无法识别则返回None
        """
        url_lower = url.lower()
        for source_type, pattern in self._SOURCE_PATTERNS.items():
            if re.search(pattern, url_lower, re.IGNORECASE):
                return source_type
        return None

    def _get_downloader(self, source_type: str) -> object:
        """
        获取对应源类型的下载器实例

        Args:
            source_type: 源类型标识符

        Returns:
            下载器实例

        Raises:
            ValueError: 不支持的媒体源类型
        """
        if source_type in self._downloaders_cache:
            return self._downloaders_cache[source_type]

        if source_type == 'bilibili':
            downloader = BilibiliDownloader(
                output_dir=self.output_dir,
                need_login=self.need_login
            )
        elif source_type == 'youtube':
            downloader = YoutubeDownloader(
                output_dir=self.output_dir,
                need_login=self.need_login
            )
        elif source_type == 'xiaoyuzhou':
            downloader = XiaoyuzhouDownloader(output_dir=self.output_dir)
        else:
            raise ValueError(f"不支持的媒体源类型: {source_type}")

        self._downloaders_cache[source_type] = downloader
        return downloader

    def download(self, url: str, progress_callback: Optional[Callable[[Dict], None]] = None) -> DownloadResult:
        """
        统一的下载接口，自动识别媒体源并执行下载

        Args:
            url: 媒体URL
            progress_callback: 进度回调函数

        Returns:
            DownloadResult: 下载结果
        """
        try:
            source_type = self._get_source_type(url)
            if not source_type:
                return DownloadResult(
                    success=False,
                    error_message=f"不支持的媒体源，无法识别URL: {url}"
                )

            logger.info(f"识别到媒体源: {source_type}，准备下载: {url}")

            downloader = self._get_downloader(source_type)

            if source_type == 'xiaoyuzhou':
                result = downloader.download_episode(url, progress_callback=progress_callback)
            else:
                result = downloader.download_video(url, progress_callback=progress_callback)

            return result

        except ValueError as e:
            logger.error(f"下载失败: {str(e)}")
            return DownloadResult(success=False, error_message=str(e))
        except Exception as e:
            logger.error(f"下载过程中发生未预期的错误: {str(e)}", exc_info=True)
            return DownloadResult(success=False, error_message=f"下载失败: {str(e)}")

    def download_bilibili(self, url: str, progress_callback: Optional[Callable[[Dict], None]] = None) -> DownloadResult:
        """
        下载B站视频，提供便捷接口

        Args:
            url: B站视频URL
            progress_callback: 进度回调函数

        Returns:
            DownloadResult: 下载结果
        """
        downloader = self._get_downloader('bilibili')
        return downloader.download_video(url, progress_callback=progress_callback)

    def download_youtube(self, url: str, progress_callback: Optional[Callable[[Dict], None]] = None) -> DownloadResult:
        """
        下载YouTube视频，提供便捷接口

        Args:
            url: YouTube视频URL
            progress_callback: 进度回调函数

        Returns:
            DownloadResult: 下载结果
        """
        downloader = self._get_downloader('youtube')
        return downloader.download_video(url, progress_callback=progress_callback)

    def download_xiaoyuzhou(self, url: str, progress_callback: Optional[Callable[[Dict], None]] = None) -> DownloadResult:
        """
        下载小宇宙播客，提供便捷接口

        Args:
            url: 小宇宙播客URL
            progress_callback: 进度回调函数

        Returns:
            DownloadResult: 下载结果
        """
        downloader = self._get_downloader('xiaoyuzhou')
        return downloader.download_episode(url, progress_callback=progress_callback)
