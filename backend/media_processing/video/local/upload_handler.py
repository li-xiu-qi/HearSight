# -*- coding: utf-8 -*-
"""本地上传视频处理"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

from backend.common_interfaces import DownloadResult

logger = logging.getLogger(__name__)

SUPPORTED_VIDEO_FORMATS = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}


def process_uploaded_video(file_path: str, output_dir: str) -> DownloadResult:
    """处理本地上传的视频文件。

    验证视频文件，并提取音频。

    Args:
        file_path: 上传文件的完整路径
        output_dir: 输出目录（用于存放提取的音频）

    Returns:
        DownloadResult: 处理结果，包含video_path和audio_path
    """
    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return DownloadResult(
                success=False,
                error_message=f"文件不存在: {file_path}"
            )

        file_ext = file_path_obj.suffix.lower()
        safe_title = file_path_obj.stem

        # 检查是否为视频文件
        if file_ext not in SUPPORTED_VIDEO_FORMATS:
            return DownloadResult(
                success=False,
                error_message=f"不支持的视频格式: {file_ext}。支持格式: {', '.join(SUPPORTED_VIDEO_FORMATS)}"
            )

        logger.info(f"上传视频文件: {file_path}，正在提取音频...")

        audio_path = _extract_audio_with_ffmpeg(file_path, safe_title, output_dir)
        if audio_path:
            logger.info(f"音频提取成功: {audio_path}")
            return DownloadResult(
                video_path=file_path,
                audio_path=audio_path,
                title=safe_title,
                media_type="both",
                success=True
            )
        else:
            logger.error("音频提取失败")
            return DownloadResult(
                success=False,
                error_message="无法从视频中提取音频"
            )

    except Exception as e:
        logger.error(f"处理上传视频文件异常: {e}", exc_info=True)
        return DownloadResult(
            success=False,
            error_message=f"处理文件失败: {str(e)}"
        )


def _extract_audio_with_ffmpeg(
    video_path: str,
    safe_title: str,
    output_dir: str
) -> Optional[str]:
    """使用ffmpeg从视频中提取音频。

    Args:
        video_path: 视频文件路径
        safe_title: 安全的标题（用于生成输出文件名）
        output_dir: 输出目录

    Returns:
        提取成功时返回音频文件路径，否则返回None
    """
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 提取为 m4a 格式
        audio_path = str(output_path / f"{safe_title}_audio.m4a")

        # 如果目标文件已存在，先删除
        if os.path.exists(audio_path):
            os.remove(audio_path)
            logger.info(f"删除已存在的音频文件: {audio_path}")

        logger.info(f"开始提取音频: 源视频={video_path}, 目标路径={audio_path}")

        # 使用m4a格式，直接复制音频流不重新编码
        cmd = [
            'ffmpeg',
            '-y',  # 强制覆盖
            '-i', video_path,
            '-vn',  # 禁用视频
            '-acodec', 'copy',  # 直接复制音频流，不重新编码
            '-loglevel', 'error',  # 只显示错误信息
            audio_path
        ]

        logger.info(f"执行ffmpeg命令提取音频: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            if not os.path.exists(audio_path):
                logger.error(f"ffmpeg声称成功但输出文件不存在: {audio_path}")
                return None

            file_size = os.path.getsize(audio_path)
            logger.info(f"音频提取成功: {audio_path} (大小: {file_size} 字节)")
            return audio_path
        else:
            logger.error(f"ffmpeg提取音频失败: returncode={result.returncode}, stderr={result.stderr}")
            return None

    except FileNotFoundError:
        logger.error("ffmpeg未安装或未在PATH中")
        return None
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg提取音频超时 (300秒)")
        return None
    except Exception as e:
        logger.error(f"ffmpeg提取音频异常: {e}", exc_info=True)
        return None
