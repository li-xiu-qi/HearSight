# -*- coding: utf-8 -*-
"""通用接口定义"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class DownloadResult:
    """下载结果"""
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    title: Optional[str] = None
    duration: Optional[float] = None
    media_type: Optional[str] = None  # "video", "audio", 或 "both"
    success: bool = False
    error_message: Optional[str] = None