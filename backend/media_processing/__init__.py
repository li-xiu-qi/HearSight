# -*- coding: utf-8 -*-
"""媒体处理模块"""

from backend.common_interfaces import DownloadResult
from .upload_handler import process_uploaded_file
from .audio.local import process_uploaded_audio
from .video.local import process_uploaded_video
from .downloader_factory import MediaDownloaderFactory

__all__ = [
    'DownloadResult',
    'MediaDownloaderFactory',
    'process_uploaded_file',
    'process_uploaded_audio',
    'process_uploaded_video',
]
