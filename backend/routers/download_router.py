# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from backend.db.job_store import check_duplicate_url
from backend.routers.progress_router import set_download_progress
from backend.services.download_service import start_download

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["download"])


@router.post("/download")
def api_download(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    """启动视频下载任务"""
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    static_dir: Path = request.app.state.static_dir
    out_dir = payload.get("out_dir") or str(static_dir)
    sessdata = payload.get("sessdata")
    playlist = bool(payload.get("playlist", False))
    quality = payload.get("quality", "best")
    workers = int(payload.get("workers", 1))
    job_id = payload.get("job_id")
    db_url = request.app.state.db_url

    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    # 检查是否存在已成功下载的相同URL
    if db_url:
        existing_job = check_duplicate_url(db_url, url)
        if existing_job:
            logger.info(f"检测到重复下载，URL已在job_id={existing_job['id']}中成功下载")
            set_download_progress(
                job_id,
                {
                    "status": "completed",
                    "stage": "downloading",
                    "progress_percent": 100.0,
                    "filename": existing_job.get("result", {}).get("basename", ""),
                    "current_bytes": 0,
                    "total_bytes": 0,
                    "speed": 0,
                    "eta_seconds": None,
                    "timestamp": "",
                    "job_id": job_id,
                    "items": existing_job.get("result", {}).get("items", []),
                    "duplicate": True,
                    "original_job_id": existing_job["id"],
                },
            )
            return {
                "status": "duplicate",
                "job_id": job_id,
                "original_job_id": existing_job["id"],
                "message": f"该URL已在任务{existing_job['id']}中成功下载，已跳过下载",
                "items": existing_job.get("result", {}).get("items", []),
            }

    # 初始化进度状态
    set_download_progress(
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

    # 启动后台下载
    start_download(
        job_id, url, out_dir, sessdata or "", playlist, quality, workers, db_url
    )

    return {
        "status": "started",
        "job_id": job_id,
        "message": "下载任务已启动，请轮询查询进度",
    }
