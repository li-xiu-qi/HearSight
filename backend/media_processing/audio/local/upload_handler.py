# -*- coding: utf-8 -*-
"""本地上传音频处理"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from backend.common_interfaces import DownloadResult

logger = logging.getLogger(__name__)

SUPPORTED_AUDIO_FORMATS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"}


def process_uploaded_audio(file_path: str) -> DownloadResult:
    """处理本地上传的音频文件。

    验证并返回音频文件路径。

    Args:
        file_path: 上传文件的完整路径

    Returns:
        DownloadResult: 处理结果，包含audio_path
    """
    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return DownloadResult(
                success=False,
                error_message=f"文件不存在: {file_path}"
            )

        file_ext = file_path_obj.suffix.lower()

        # 检查是否为音频文件
        if file_ext not in SUPPORTED_AUDIO_FORMATS:
            return DownloadResult(
                success=False,
                error_message=f"不支持的音频格式: {file_ext}。支持格式: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
            )

        # 验证文件能被打开
        try:
            with open(file_path, "rb") as f:
                file_size = os.path.getsize(file_path)
        except IOError as e:
            return DownloadResult(
                success=False,
                error_message=f"无法打开音频文件: {str(e)}"
            )

        logger.info(f"上传音频文件: {file_path} (格式: {file_ext}, 大小: {file_size} 字节)")
        return DownloadResult(
            audio_path=file_path,
            title=file_path_obj.stem,
            media_type="audio",
            success=True
        )

    except Exception as e:
        logger.error(f"处理上传音频文件异常: {e}", exc_info=True)
        return DownloadResult(
            success=False,
            error_message=f"处理文件失败: {str(e)}"
        )
