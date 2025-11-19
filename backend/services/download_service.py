# -*- coding: utf-8 -*-
"""
下载服务模块。

提供异步下载功能，封装了下载线程管理和进度上报逻辑。
主要用于处理媒体文件的下载任务，支持多平台URL。

主要组件：
- _download_worker: 后台下载工作函数
- start_download: 启动下载线程的接口函数

依赖：
- MultiPlatformDownloader: 多平台下载器
- progress_router: 进度上报路由
- job_store: 数据库存储
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Dict, List
from typing_extensions import TypedDict


# 数据结构定义
class ProgressInfo(TypedDict):
    """下载进度信息结构，从下载器回调中接收的原始进度数据"""

    status: str  # 下载状态：'downloading', 'finished', 'error' 等
    progress_percent: float  # 下载进度百分比 (0-100)
    downloaded_bytes: int  # 已下载的字节数
    total_bytes: int  # 文件总字节数
    speed: float  # 下载速度 (字节/秒)
    eta_seconds: int | None  # 预计剩余时间 (秒)，None表示未知
    filename: str  # 当前下载的文件名
    timestamp: str  # 时间戳字符串，目前为空字符串


class ProgressData(TypedDict, total=False):
    """进度上报数据结构，发送给前端的标准化进度信息"""

    stage: str  # 处理阶段，如 'downloading'
    job_id: int  # 任务ID，用于标识具体任务
    status: str  # 任务状态：'in-progress', 'completed', 'error' 等
    progress_percent: float  # 进度百分比 (0-100)
    filename: str  # 文件名
    current_bytes: int  # 当前已处理的字节数
    total_bytes: int  # 总字节数
    speed: float  # 处理速度 (字节/秒)
    eta_seconds: int | None  # 预计剩余时间 (秒)
    timestamp: str  # 时间戳
    items: List[ResultItem]  # 可选：完成时的下载结果项列表
    error: str  # 可选：错误信息描述


class ResultItem(TypedDict):
    """下载结果项结构，表示单个下载完成的文件信息"""

    path: str  # 文件的绝对路径
    basename: str  # 文件的基本名称 (不含路径)
    static_url: str  # 静态文件服务的访问URL


from backend.db.job_store import update_job_result
from backend.routers.progress_router import set_task_progress
from backend.media_file_download.downloader_factory import MediaDownloaderFactory

logger = logging.getLogger(__name__)


def _download_worker(
    job_id: int,
    url: str,
    out_dir: str,
    db_url: str | None,
) -> None:
    """
    后台下载工作函数，在单独线程中执行下载任务。

    负责初始化下载器、执行下载、处理进度回调、
    更新任务状态和数据库记录。

    Args:
        job_id: 任务ID，用于进度跟踪和数据库更新
        url: 要下载的媒体URL
        out_dir: 输出目录路径
        db_url: 数据库连接URL，可选，用于更新任务结果
    """

    def progress_hook(progress_info: Dict[str, Any]):
        """
        下载进度回调钩子。

        将下载器的进度信息转换为标准格式并上报给进度路由。
        同时记录调试日志。

        Args:
            progress_info: 下载器提供的进度信息字典
        """
        progress_data: ProgressData = {
            "stage": "downloading",
            "job_id": job_id,
            "status": (
                "in-progress"
                if progress_info["status"] == "downloading"
                else progress_info["status"]
            ),
            "progress_percent": progress_info.get("progress_percent", 0),
            "filename": progress_info.get("filename", ""),
            "current_bytes": progress_info.get("downloaded_bytes", 0),
            "total_bytes": progress_info.get("total_bytes", 0),
            "speed": progress_info.get("speed", 0),
            "eta_seconds": progress_info.get("eta_seconds"),
            "timestamp": progress_info.get("timestamp", ""),
        }
        set_task_progress(job_id, progress_data)
        try:
            pct = float(progress_info.get("progress_percent", 0))
        except Exception:
            pct = 0.0
        logger.debug(f"下载进度 (job_id={job_id}): {pct:.1f}%")

    try:
        logger.info(f"开始下载任务 (job_id={job_id}): {url}")
        # 初始化下载工厂，传入进度回调
        factory = MediaDownloaderFactory(output_dir=out_dir)
        # 执行下载，返回DownloadResult
        result = factory.download(url, progress_callback=progress_hook)

        if not result.success:
            raise RuntimeError(f"下载失败: {result.error_message}")

        file_path = result.video_path or result.audio_path
        if not file_path:
            raise RuntimeError("下载结果为空")

        logger.info(f"下载完成 (job_id={job_id}): {file_path}")

        # 构建结果项列表，包含文件路径和静态URL
        result_items: List[ResultItem] = []
        p = Path(file_path)
        result_items.append(
            {
                "path": str(p.resolve()),  # 绝对路径
                "basename": p.name,  # 文件名
                "static_url": f"/static/{p.name}",  # 静态服务URL
            }
        )

        # 更新进度为完成状态
        set_task_progress(
            job_id,
            {
                "status": "completed",
                "stage": "downloading",
                "progress_percent": 100.0,
                "filename": result_items[0]["basename"] if result_items else "",
                "current_bytes": 0,
                "total_bytes": 0,
                "speed": 0,
                "eta_seconds": None,
                "timestamp": "",
                "job_id": job_id,
                "items": result_items,
            },
        )

        # 如果提供了数据库URL，更新数据库中的任务结果
        if db_url:
            update_job_result(db_url, job_id, {"items": result_items})

    except Exception as e:
        # 记录错误日志，包含完整的异常信息
        logger.error(f"下载任务失败 (job_id={job_id}): {e}", exc_info=True)
        # 更新进度为错误状态
        set_task_progress(
            job_id,
            {
                "status": "error",
                "stage": "downloading",
                "progress_percent": 0,
                "filename": "",
                "current_bytes": 0,
                "total_bytes": 0,
                "speed": 0,
                "eta_seconds": None,
                "timestamp": "",
                "job_id": job_id,
                "error": str(e),  # 错误信息
            },
        )


def start_download(
    job_id: int,
    url: str,
    out_dir: str,
    db_url: str | None,
) -> None:
    """
    启动后台下载线程。

    创建一个守护线程来执行下载任务，不阻塞调用者。
    线程将在后台异步执行下载工作。

    Args:
        job_id: 任务ID
        url: 下载URL
        out_dir: 输出目录
        db_url: 数据库URL，可选
    """
    # 创建守护线程，确保程序退出时线程也会终止
    t = threading.Thread(
        target=_download_worker,
        args=(job_id, url, out_dir, db_url),
        daemon=True,
    )
    t.start()
