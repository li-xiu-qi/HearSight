# -*- coding: utf-8 -*-
"""进度更新工具函数"""

import json
from typing import Dict, Any


def update_task_progress(set_task_progress_func, redis_client, job_id: int, progress_info: Dict[str, Any]) -> bool:
    """统一的进度更新函数，包含fallback逻辑"""
    ok = set_task_progress_func(
        job_id,
        progress_info,
    )
    if not ok:
        try:
            redis_client.setex(f"task_progress:{job_id}", 86400, json.dumps(progress_info, ensure_ascii=False))
        except Exception:
            pass
    return ok


def create_progress_info(job_id: int, status: str, stage: str, progress_percent: int,
                        filename: str = "", message: str = "", **kwargs) -> Dict[str, Any]:
    """创建进度信息字典"""
    return {
        "status": status,
        "stage": stage,
        "progress_percent": progress_percent,
        "filename": filename,
        "message": message,
        "job_id": job_id,
        **kwargs
    }