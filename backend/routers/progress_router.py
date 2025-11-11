"""下载和处理进度查询路由"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from fastapi import APIRouter

# 数据结构定义
class ProgressData(TypedDict, total=False):
    """进度数据结构"""
    status: str  # 任务状态
    stage: str  # 处理阶段
    progress_percent: float  # 进度百分比
    filename: str  # 文件名
    message: str  # 状态消息
    job_id: int  # 任务ID
    current_bytes: int  # 当前已处理的字节数
    total_bytes: int  # 总字节数
    speed: float  # 处理速度
    eta_seconds: Optional[int]  # 预计剩余时间
    timestamp: str  # 时间戳
    items: List[Dict[str, Any]]  # 结果项列表
    error: str  # 错误信息
    duplicate: bool  # 是否为重复任务
    original_job_id: int  # 原始任务ID


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["progress"])

# 存储任务的进度信息（包括下载和ASR阶段）
task_progress: Dict[int, Dict[str, Any]] = {}


def get_task_progress(job_id: int) -> ProgressData:
    """获取任务进度（包括下载和ASR阶段）"""
    if job_id not in task_progress:
        return {
            "status": "idle",
            "stage": "waiting",
            "progress_percent": 0,
            "filename": "",
            "message": "等待处理",
        }
    return task_progress[job_id]


def set_task_progress(job_id: int, progress: ProgressData) -> None:
    """设置任务进度"""
    task_progress[job_id] = progress
    logger.debug(
        f"更新任务进度 job_id={job_id}: {progress.get('stage')} - {progress.get('message', '')}"
    )


@router.get("/progress/download/{job_id}")
def api_get_download_progress(job_id: int) -> ProgressData:
    """查询下载进度"""
    return get_task_progress(job_id)


@router.get("/progress/task/{job_id}")
def api_get_task_progress(job_id: int) -> ProgressData:
    """查询任务进度（包括下载和ASR阶段）"""
    return get_task_progress(job_id)
