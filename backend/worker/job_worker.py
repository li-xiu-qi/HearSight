# -*- coding: utf-8 -*-
"""后台任务处理 worker"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Dict

from fastapi import FastAPI

from backend.audio2text.asr_sentence_segments import process as asr_process
from backend.db.job_store import (
    claim_next_pending_job,
    finish_job_failed,
    finish_job_success,
    get_job,
    update_job_result,
    update_job_status,
)
from backend.db.transcript_crud import save_transcript
from backend.routers.progress_router import set_task_progress
from backend.utils.vedio_utils.download_video.multi_platform_downloader import (
    MultiPlatformDownloader,
)


def job_worker(app: FastAPI, db_url: str | None) -> None:
    """后台 worker 主循环。

    处理待处理任务，执行下载 + ASR 两个阶段。
    """
    static_dir: Path = app.state.static_dir

    while True:
        job = claim_next_pending_job(db_url)
        if not job:
            time.sleep(1.0)
            continue

        job_id = int(job["id"])
        url = str(job["url"])

        try:
            _process_job(db_url, job_id, url, static_dir)
        except Exception as e:
            finish_job_failed(db_url, job_id, str(e))


def _process_job(db_url: str | None, job_id: int, url: str, static_dir: Path) -> None:
    """处理单个任务。

    分两阶段执行：
    1. 下载阶段：下载视频并记录 media_path (如果是上传文件则跳过)
    2. ASR 阶段：执行语音识别并保存 transcript
    """
    # 读取当前任务的结果，用于阶段性恢复
    info = get_job(db_url, job_id) or {}
    res = dict(info.get("result") or {})

    # Step A: 下载阶段
    media_path = res.get("media_path")
    if not media_path or not Path(str(media_path)).exists():
        # 检查是否是上传的文件
        if url.startswith("upload://"):
            basename = url.replace("upload://", "")
            media_path = str((static_dir / basename).resolve())

            if not Path(media_path).exists():
                raise RuntimeError(f"上传文件不存在: {media_path}")

            # 上传文件跳过下载阶段,直接标记为准备ASR
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

            res.update(
                {
                    "media_path": media_path,
                    "basename": basename,
                    "static_url": f"/static/{basename}",
                    "source": "upload",
                }
            )
            update_job_result(
                db_url,
                job_id,
                {
                    "media_path": media_path,
                    "basename": basename,
                    "static_url": f"/static/{basename}",
                    "source": "upload",
                },
            )
        else:
            update_job_status(db_url, job_id, "downloading")

            def on_progress(info: Dict) -> None:
                """下载进度回调"""
                set_task_progress(
                    job_id,
                    {
                        "status": info["status"],
                        "stage": "download",
                        "progress_percent": info["progress_percent"],
                        "current_bytes": info["downloaded_bytes"],
                        "total_bytes": info["total_bytes"],
                        "speed": info["speed"],
                        "eta_seconds": info["eta_seconds"],
                        "filename": info["filename"],
                        "job_id": job_id,
                    },
                )

            downloader = MultiPlatformDownloader(
                url=url,
                out_dir=str(static_dir),
                progress_callback=on_progress,
            )
            files = downloader.download()
            if not files:
                raise RuntimeError("下载结果为空")

            media_path = str(Path(files[0]).resolve())
            basename = Path(media_path).name

            set_task_progress(
                job_id,
                {
                    "status": "ready",
                    "stage": "download",
                    "progress_percent": 100,
                    "filename": basename,
                    "message": "下载完成,准备进行语音识别",
                    "job_id": job_id,
                },
            )

            res.update(
                {
                    "media_path": media_path,
                    "basename": basename,
                    "static_url": f"/static/{basename}",
                    "source": "download",
                }
            )
            update_job_result(
                db_url,
                job_id,
                {
                    "media_path": media_path,
                    "basename": basename,
                    "static_url": f"/static/{basename}",
                    "source": "download",
                },
            )
    else:
        basename = Path(str(media_path)).name

    # 检测媒体类型
    media_ext = Path(str(media_path)).suffix.lower()
    audio_extensions = {".m4a", ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"}
    media_type = "audio" if media_ext in audio_extensions else "video"

    # Step B: ASR 阶段
    if not res.get("transcript_id"):
        update_job_status(db_url, job_id, "processing")

        set_task_progress(
            job_id,
            {
                "status": "processing",
                "stage": "asr",
                "progress_percent": 0,
                "filename": basename,
                "message": "正在进行语音识别,请稍候...",
                "job_id": job_id,
            },
        )

        segs = asr_process(str(media_path))

        set_task_progress(
            job_id,
            {
                "status": "processing",
                "stage": "asr",
                "progress_percent": 50,
                "filename": basename,
                "message": "语音识别完成,正在保存结果...",
                "job_id": job_id,
            },
        )

        transcript_id = save_transcript(db_url, str(media_path), segs, media_type)
        res.update({"transcript_id": transcript_id, "media_type": media_type})
        update_job_result(
            db_url, job_id, {"transcript_id": transcript_id, "media_type": media_type}
        )

        set_task_progress(
            job_id,
            {
                "status": "completed",
                "stage": "asr",
                "progress_percent": 100,
                "filename": basename,
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
            "filename": basename,
            "message": "任务处理完成",
            "job_id": job_id,
        },
    )


def start_worker(app: FastAPI, db_url: str | None) -> None:
    """启动后台 worker 线程。"""
    t = threading.Thread(target=job_worker, args=(app, db_url), daemon=True)
    t.start()
