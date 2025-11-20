# -*- coding: utf-8 -*-
"""媒体处理适配器 - 提供向后兼容的接口"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .common_interfaces import DownloadResult
from .audio.local.upload_handler import process_uploaded_audio, SUPPORTED_AUDIO_FORMATS
from .video.local.upload_handler import process_uploaded_video, SUPPORTED_VIDEO_FORMATS


def process_uploaded_file(file_path: str, output_dir: str) -> DownloadResult:
    """处理本地上传的文件 - 兼容接口。

    根据文件类型自动调用对应的处理器。
    对于音频文件，直接返回路径。
    对于视频文件，提取音频并返回两个路径。

    Args:
        file_path: 上传文件的完整路径
        output_dir: 输出目录（用于存放提取的音频）

    Returns:
        DownloadResult: 处理结果，包含audio_path和video_path
    """
    file_path_obj = Path(file_path)
    file_ext = file_path_obj.suffix.lower()

    if file_ext in SUPPORTED_AUDIO_FORMATS:
        return process_uploaded_audio(file_path)
    elif file_ext in SUPPORTED_VIDEO_FORMATS:
        return process_uploaded_video(file_path, output_dir)
    else:
        return DownloadResult(
            success=False,
            error_message=f"不支持的文件格式: {file_ext}。支持音频格式: {SUPPORTED_AUDIO_FORMATS}，视频格式: {SUPPORTED_VIDEO_FORMATS}"
        )
