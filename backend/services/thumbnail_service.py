# -*- coding: utf-8 -*-
"""视频缩略图生成服务"""

from __future__ import annotations

import base64
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def generate_thumbnail_ffmpeg(
    video_path: str, time_ms: float, width: int = 320, quality: int = 5
) -> Optional[str]:
    """
    使用 ffmpeg 从视频指定时间生成缩略图，返回 base64 编码的 JPEG 图片

    Args:
        video_path: 视频文件路径
        time_ms: 时间点（毫秒）
        width: 缩略图宽度（高度自动计算保持比例）
        quality: JPEG 质量（2-31，数字越小质量越高）

    Returns:
        base64 编码的图片数据，格式: data:image/jpeg;base64,xxx
        失败返回 None
    """
    video_file = Path(video_path)
    if not video_file.exists():
        logger.error(f"视频文件不存在: {video_path}")
        return None

    # 转换毫秒为秒
    time_sec = time_ms / 1000.0

    try:
        # 创建临时文件保存截图
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        # ffmpeg 命令：跳转到指定时间，提取一帧，缩放并保存
        cmd = [
            "ffmpeg",
            "-ss",
            str(time_sec),  # 跳转到指定时间
            "-i",
            str(video_file),  # 输入文件
            "-frames:v",
            "1",  # 只提取一帧
            "-vf",
            f"scale={width}:-1",  # 缩放，保持宽高比
            "-c:v",
            "png",  # 用PNG编码器代替MJPEG
            "-y",  # 覆盖输出文件
            tmp_path,
        ]

        logger.info(f"生成缩略图: {video_path} @ {time_sec}s")

        # 执行 ffmpeg 命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10,  # 10秒超时
        )

        if result.returncode != 0:
            logger.error(f"ffmpeg 执行失败: {result.stderr}")
            return None

        # 读取生成的图片并转换为 base64
        tmp_file_path = Path(tmp_path)
        if not tmp_file_path.exists():
            logger.error(f"缩略图文件未生成: {tmp_path}")
            return None

        with open(tmp_path, "rb") as f:
            image_data = f.read()

        # 删除临时文件
        tmp_file_path.unlink()

        # 转换为 base64
        base64_data = base64.b64encode(image_data).decode("utf-8")
        data_url = f"data:image/png;base64,{base64_data}"

        logger.info(f"缩略图生成成功，大小: {len(image_data)} bytes")
        return data_url

    except subprocess.TimeoutExpired:
        logger.error(f"ffmpeg 执行超时: {video_path} @ {time_sec}s")
        return None
    except Exception as e:
        logger.error(f"生成缩略图失败: {e}")
        return None


def generate_thumbnail_pillow(
    video_path: str, time_ms: float, width: int = 320
) -> Optional[str]:
    """
    使用 OpenCV + Pillow 从视频指定时间生成缩略图（备用方案）

    需要安装: pip install opencv-python pillow
    """
    try:
        import io

        import cv2
        from PIL import Image

        video_file = Path(video_path)
        if not video_file.exists():
            logger.error(f"视频文件不存在: {video_path}")
            return None

        # 打开视频
        cap = cv2.VideoCapture(str(video_file))
        if not cap.isOpened():
            logger.error(f"无法打开视频文件: {video_path}")
            return None

        # 设置到指定时间（毫秒）
        cap.set(cv2.CAP_PROP_POS_MSEC, time_ms)

        # 读取帧
        ret, frame = cap.read()
        cap.release()

        if not ret:
            logger.error(f"无法读取视频帧: {video_path} @ {time_ms}ms")
            return None

        # 转换 BGR 到 RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 转换为 PIL Image
        image = Image.fromarray(frame_rgb)

        # 缩放图片
        height = int(image.height * width / image.width)
        image = image.resize((width, height), Image.LANCZOS)

        # 转换为 JPEG base64
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=80)
        image_data = buffer.getvalue()

        base64_data = base64.b64encode(image_data).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{base64_data}"

        logger.info(f"缩略图生成成功（Pillow），大小: {len(image_data)} bytes")
        return data_url

    except ImportError:
        logger.warning("未安装 opencv-python 或 pillow，无法使用 Pillow 方式生成缩略图")
        return None
    except Exception as e:
        logger.error(f"生成缩略图失败（Pillow）: {e}")
        return None


def generate_thumbnail(
    video_path: str, start_time_ms: float, end_time_ms: float, width: int = 320
) -> Optional[str]:
    """
    生成视频缩略图（优先使用 ffmpeg，失败则尝试 Pillow）

    Args:
        video_path: 视频文件路径
        start_time_ms: 开始时间（毫秒）
        end_time_ms: 结束时间（毫秒）
        width: 缩略图宽度

    Returns:
        base64 编码的图片数据 URL
    """
    # 使用中点时间
    mid_time_ms = (start_time_ms + end_time_ms) / 2

    # 优先使用 ffmpeg
    result = generate_thumbnail_ffmpeg(video_path, mid_time_ms, width)

    # 如果 ffmpeg 失败，尝试 Pillow
    if result is None:
        logger.warning("ffmpeg 生成缩略图失败，尝试使用 Pillow")
        result = generate_thumbnail_pillow(video_path, mid_time_ms, width)

    return result
