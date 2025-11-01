# -*- coding: utf-8 -*-
"""
上传相关服务函数：
- create_audio_placeholder: 为音频文件创建占位符图片
- get_unique_filename: 在目录下生成不冲突的唯一文件名
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def create_audio_placeholder(output_path: Path, duration: float = 0) -> None:
    """为音频文件创建占位符图片"""
    width, height = 1280, 720
    img = Image.new("RGB", (width, height), color=(45, 55, 72))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 60)
        small_font = ImageFont.truetype("arial.ttf", 30)
    except Exception:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    text = "Audio File"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) / 2
    y = (height - text_height) / 2 - 50

    draw.text((x, y), text, fill=(203, 213, 225), font=font)

    subtitle = "Playing audio content"
    bbox2 = draw.textbbox((0, 0), subtitle, font=small_font)
    sub_width = bbox2[2] - bbox2[0]
    sub_x = (width - sub_width) / 2
    sub_y = y + text_height + 30
    draw.text((sub_x, sub_y), subtitle, fill=(148, 163, 184), font=small_font)

    img.save(output_path)
    logger.info(f"创建音频占位符图片: {output_path}")


def get_unique_filename(directory: Path, filename: str) -> str:
    """生成唯一文件名,如果存在冲突则添加后缀"""
    file_path = directory / filename
    if not file_path.exists():
        return filename

    stem = Path(filename).stem
    ext = Path(filename).suffix
    counter = 1

    while True:
        new_filename = f"{stem}-{counter}{ext}"
        new_path = directory / new_filename
        if not new_path.exists():
            return new_filename
        counter += 1
