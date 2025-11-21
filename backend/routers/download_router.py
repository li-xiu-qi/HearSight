# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException, Request
from typing_extensions import TypedDict

from backend.routers.progress_router import set_task_progress
from backend.queues.tasks import process_job_task


# 数据结构定义
class DownloadRequest(TypedDict, total=False):
    """下载请求数据结构"""

    url: str  # 下载URL
    out_dir: str  # 输出目录（可选）
    job_id: int  # 任务ID


class DownloadResultItem(TypedDict):
    """下载结果项数据结构"""

    path: str  # 文件绝对路径
    basename: str  # 文件名
    static_url: str  # 静态文件URL


class DownloadDuplicateResponse(TypedDict):
    """重复下载响应数据结构"""

    status: str  # "duplicate"
    job_id: int  # 当前任务ID
    original_job_id: int  # 原始任务ID
    message: str  # 提示消息
    items: List[DownloadResultItem]  # 下载结果项


class DownloadStartedResponse(TypedDict):
    """下载启动响应数据结构"""

    status: str  # "started"
    job_id: int  # 任务ID
    task_id: str  # Celery任务ID
    message: str  # 提示消息


DownloadResponse = Union[DownloadDuplicateResponse, DownloadStartedResponse]

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["download"])


@router.post("/download")
def api_download(payload: DownloadRequest, request: Request) -> DownloadResponse:
    """启动视频下载任务（异步处理）"""
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    static_dir: Path = request.app.state.static_dir
    out_dir = payload.get("out_dir") or str(static_dir)
    job_id = payload.get("job_id")
    db_url = request.app.state.db_url

    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    # 初始化进度状态
    set_task_progress(
        job_id,
        {
            "status": "in-progress",
            "stage": "downloading",
            "progress_percent": 0,
            "filename": "",
            "current_bytes": 0,
            "total_bytes": 0,
            "speed": 0,
            "eta_seconds": None,
            "timestamp": "",
            "job_id": job_id,
        },
    )

    # 提交Celery异步任务
    try:
        task = process_job_task.delay(
            job_id=job_id,
            url=url,
            static_dir=str(static_dir),
            db_url=db_url,
        )
        logger.info(f"任务已提交到Celery，job_id={job_id}, task_id={task.id}")

        return {
            "status": "started",
            "job_id": job_id,
            "task_id": task.id,
            "message": "任务已提交，后台异步处理中",
        }
    except Exception as e:
        logger.error(f"提交Celery任务失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")


