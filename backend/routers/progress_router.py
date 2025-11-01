"""下载和处理进度查询路由"""
from __future__ import annotations

from fastapi import APIRouter
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["progress"])

# 存储任务的进度信息（包括下载和ASR阶段）
task_progress: Dict[int, Dict[str, Any]] = {}


def get_task_progress(job_id: int) -> Dict[str, Any]:
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


def set_task_progress(job_id: int, progress: Dict[str, Any]) -> None:
    """设置任务进度"""
    task_progress[job_id] = progress
    logger.debug(f"更新任务进度 job_id={job_id}: {progress.get('stage')} - {progress.get('message', '')}")


# 保留旧名称以兼容现有代码
def get_download_progress(job_id: int) -> Dict[str, Any]:
    """获取下载进度（兼容旧接口）"""
    return get_task_progress(job_id)


def set_download_progress(job_id: int, progress: Dict[str, Any]) -> None:
    """设置下载进度（兼容旧接口）"""
    set_task_progress(job_id, progress)


@router.get("/progress/download/{job_id}")
def api_get_download_progress(job_id: int) -> Dict[str, Any]:
    """查询下载进度"""
    return get_download_progress(job_id)


@router.get("/progress/task/{job_id}")
def api_get_task_progress(job_id: int) -> Dict[str, Any]:
    """查询任务进度（包括下载和ASR阶段）"""
    return get_task_progress(job_id)

