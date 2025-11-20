# -*- coding: utf-8 -*-
"""Celery异步任务定义"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from backend.config import create_celery_app
from backend.audio2text.asr_sentence_segments import process as asr_process
from backend.db.job_store import (
    finish_job_failed,
    finish_job_success,
    get_job,
    update_job_result,
    update_job_status,
)
from backend.db.transcript_crud import save_transcript
from backend.media_processing import MediaDownloaderFactory, process_uploaded_file

# 创建Celery应用实例
app = create_celery_app()


@app.task(
    bind=True,
    name="backend.queues.tasks.process_job_task",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
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
    from backend.routers.progress_router import set_task_progress

    try:
        static_path = Path(static_dir)

        # 读取当前任务的结果，用于阶段性恢复
        info = get_job(db_url, job_id) or {}
        res = dict(info.get("result") or {})

        # Step A: 下载阶段
        audio_path = res.get("audio_path")
        video_path = res.get("video_path")
        
        if not audio_path or not Path(str(audio_path)).exists():
            # 检查是否是上传的文件
            if url.startswith("upload://"):
                basename = url.replace("upload://", "")
                file_path = str((static_path / basename).resolve())

                if not Path(file_path).exists():
                    raise RuntimeError(f"上传文件不存在: {file_path}")

                # 处理上传文件（提取音频等）
                result = process_uploaded_file(file_path, str(static_path))
                if not result.success:
                    raise RuntimeError(f"处理上传文件失败: {result.error_message}")

                audio_path = result.audio_path
                video_path = result.video_path
                media_type = result.media_type

                # 标记为准备ASR
                set_task_progress(
                    job_id,
                    {
                        "status": "ready",
                        "stage": "upload",
                        "progress_percent": 100,
                        "filename": basename,
                        "message": "文件已上传,准备进行语音识别",
                        "job_id": job_id,
                    },
                )

                update_data = {
                    "audio_path": audio_path,
                    "basename": basename,
                    "static_url": f"/static/{basename}",
                    "source": "upload",
                }
                if video_path:
                    update_data["video_path"] = video_path

                res.update(update_data)
                update_job_result(db_url, job_id, update_data)
            else:
                update_job_status(db_url, job_id, "pending")

                def on_progress(info: Dict) -> None:
                    """下载进度回调"""
                    set_task_progress(
                        job_id,
                        {
                            "status": info.get("status", "unknown"),
                            "stage": "download",
                            "progress_percent": info.get("progress_percent", 0),
                            "current_bytes": info.get("downloaded_bytes", 0),
                            "total_bytes": info.get("total_bytes", 0),
                            "speed": info.get("speed", 0),
                            "eta_seconds": info.get("eta_seconds", 0),
                            "filename": info.get("filename", ""),
                            "job_id": job_id,
                        },
                    )

                factory = MediaDownloaderFactory(output_dir=str(static_path))
                result = factory.download(url, progress_callback=on_progress)
                if not result.success:
                    raise RuntimeError(f"下载失败: {result.error_message}")

                # 分别保存video_path和audio_path
                if result.audio_path:
                    audio_path = str(Path(result.audio_path).resolve())
                if result.video_path:
                    video_path = str(Path(result.video_path).resolve())
                
                if not audio_path:
                    raise RuntimeError("下载结果中没有音频文件")

                audio_basename = Path(audio_path).name

                set_task_progress(
                    job_id,
                    {
                        "status": "ready",
                        "stage": "download",
                        "progress_percent": 100,
                        "filename": audio_basename,
                        "message": "下载完成,准备进行语音识别",
                        "job_id": job_id,
                    },
                )

                update_data = {"audio_path": audio_path, "basename": audio_basename}
                if video_path:
                    update_data["video_path"] = video_path
                    update_data["static_url"] = f"/static/{Path(video_path).name}"
                else:
                    update_data["static_url"] = f"/static/{audio_basename}"
                update_data["source"] = "download"
                
                res.update(update_data)
                update_job_result(db_url, job_id, update_data)
        else:
            audio_basename = Path(str(audio_path)).name

        # Step B: ASR 阶段
        if not res.get("transcript_id"):
            update_job_status(db_url, job_id, "processing")

            set_task_progress(
                job_id,
                {
                    "status": "processing",
                    "stage": "asr",
                    "progress_percent": 0,
                    "filename": audio_basename,
                    "message": "正在进行语音识别,请稍候...",
                    "job_id": job_id,
                },
            )

            segs = asr_process(str(audio_path))

            set_task_progress(
                job_id,
                {
                    "status": "processing",
                    "stage": "asr",
                    "progress_percent": 50,
                    "filename": audio_basename,
                    "message": "语音识别完成,正在保存结果...",
                    "job_id": job_id,
                },
            )

            transcript_id = save_transcript(db_url, str(audio_path), segs, "audio", video_path=video_path if video_path else None)
            res.update({"transcript_id": transcript_id, "media_type": "audio"})
            update_job_result(
                db_url, job_id, {"transcript_id": transcript_id, "media_type": "audio"}
            )

            set_task_progress(
                job_id,
                {
                    "status": "completed",
                    "stage": "asr",
                    "progress_percent": 100,
                    "filename": audio_basename,
                    "message": "语音识别完成",
                    "job_id": job_id,
                },
            )

        # Step C: 完成任务
        finish_job_success(db_url, job_id, res)

        set_task_progress(
            job_id,
            {
                "status": "success",
                "stage": "completed",
                "progress_percent": 100,
                "filename": audio_basename,
                "message": "任务处理完成",
                "job_id": job_id,
            },
        )

        return res

    except Exception as e:
        finish_job_failed(db_url, job_id, str(e))
        raise
