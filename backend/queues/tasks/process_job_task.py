# -*- coding: utf-8 -*-
"""Celery异步任务定义"""

from __future__ import annotations

from pathlib import Path
import logging
from typing import Any, Dict, Optional

from backend.config import create_celery_app
from backend.db.job_store import (
    finish_job_failed,
    finish_job_success,
    get_job,
    update_job_status,
)
from .download_stage import handle_download_stage
from .asr_stage import handle_asr_stage
from .knowledge_base_stage import handle_knowledge_base_stage
from .progress_utils import update_task_progress, create_progress_info

# 创建Celery应用实例
app = create_celery_app()


@app.task(
    bind=True,
    name="backend.queues.tasks.process_job_task",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 1},
    retry_backoff=True,
)
def process_job_task(
    self,
    job_id: int,
    url: str,
    static_dir: str,
    db_url: Optional[str] = None,
) -> Dict[str, Any]:
    """处理单个任务的Celery任务。

    分两阶段执行：
    1. 下载阶段：下载视频并记录media_path（如果是上传文件则跳过）
    2. ASR阶段：执行语音识别并保存transcript

    Args:
        job_id: 任务ID
        url: 任务URL或upload://路径
        static_dir: 静态文件目录
        db_url: 数据库连接URL

    Returns:
        任务结果字典
    """
    # 延迟导入以避免循环依赖
    from backend.routers.progress_router import set_task_progress, redis_client as progress_redis_client
    import json
    logger = logging.getLogger(__name__)

    try:
        static_path = Path(static_dir)

        # 读取当前任务的结果，用于阶段性恢复
        info = get_job(db_url, job_id) or {}
        res = dict(info.get("result") or {})

        # Step A: 下载/上传阶段
        audio_path = res.get("audio_path")
        video_path = res.get("video_path")

        if not audio_path or not Path(str(audio_path)).exists():
            download_result = handle_download_stage(
                url, static_path, job_id, set_task_progress, progress_redis_client, db_url
            )
            res.update(download_result)
            audio_path = download_result["audio_path"]
            video_path = download_result.get("video_path")
        else:
            audio_basename = Path(str(audio_path)).name

        # Step B: ASR 阶段
        if not res.get("transcript_id"):
            update_job_status(db_url, job_id, "processing")

            media_type = res.get("media_type", "audio")
            audio_basename = res.get("basename") or Path(str(audio_path)).name

            transcript_id, segs = handle_asr_stage(
                str(audio_path), video_path, media_type, audio_basename,
                job_id, set_task_progress, progress_redis_client, db_url
            )

            res.update({"transcript_id": transcript_id, "media_type": media_type})

            # 将转写句子段添加到知识库
            handle_knowledge_base_stage(job_id, transcript_id, segs)

        # Step C: 完成任务
        finish_job_success(db_url, job_id, res)

        audio_basename = res.get("basename") or Path(str(audio_path)).name
        progress_info = create_progress_info(
            job_id, "success", "completed", 100,
            filename=audio_basename, message="任务处理完成"
        )
        update_task_progress(set_task_progress, progress_redis_client, job_id, progress_info)

        return res

    except Exception as e:
        # 设置失败进度
        progress_info = create_progress_info(
            job_id, "failed", "error", 0,
            message=f"任务处理失败: {str(e)}",
            error=str(e)
        )
        update_task_progress(set_task_progress, progress_redis_client, job_id, progress_info)

        finish_job_failed(db_url, job_id, str(e))
        raise