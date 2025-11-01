# -*- coding: utf-8 -*-
"""
下载服务：封装下载线程与进度上报逻辑，供路由调用。
"""
from __future__ import annotations

from pathlib import Path
import logging
import threading
from typing import Any, Dict, List

from backend.utils.vedio_utils.download_video.download_bilibili_with_progress import (
    download_bilibili_with_progress,
)
from backend.routers.progress_router import set_download_progress
from backend.db.pg_store import update_job_result

logger = logging.getLogger(__name__)


def _download_worker(
    job_id: int,
    url: str,
    out_dir: str,
    sessdata: str,
    playlist: bool,
    quality: str,
    workers: int,
    db_url: str | None,
) -> None:
    """后台下载任务"""

    def progress_hook(progress_info: Dict[str, Any]):
        """进度钩子，更新进度信息"""
        progress_data = {
            "stage": "downloading",
            "job_id": job_id,
            "status": "in-progress",
            "progress_percent": progress_info.get("progress_percent", 0),
            "filename": progress_info.get("filename", ""),
            "current_bytes": progress_info.get("downloaded_bytes", 0),
            "total_bytes": progress_info.get("total_bytes", 0),
            "speed": progress_info.get("speed", 0),
            "eta_seconds": progress_info.get("eta_seconds"),
            "timestamp": progress_info.get("timestamp", ""),
        }
        set_download_progress(job_id, progress_data)
        try:
            pct = float(progress_info.get("progress_percent", 0))
        except Exception:
            pct = 0.0
        logger.debug(f"下载进度 (job_id={job_id}): {pct:.1f}%")

    try:
        logger.info(f"开始下载任务 (job_id={job_id}): {url}")
        files: List[str] = download_bilibili_with_progress(
            url=url,
            out_dir=out_dir,
            progress_callback=progress_hook,
            sessdata=sessdata,
            playlist=playlist,
            quality=quality,
            workers=workers,
            use_nopart=True,
            simple_filename=True,
        )

        logger.info(f"下载完成 (job_id={job_id}): {len(files)} 个文件")

        # 更新进度为完成
        result_items = []
        for fp in files:
            p = Path(fp)
            result_items.append({
                "path": str(p.resolve()),
                "basename": p.name,
                "static_url": f"/static/{p.name}",
            })

        set_download_progress(job_id, {
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
        })

        # 更新数据库中的任务结果
        if db_url:
            update_job_result(db_url, job_id, {"items": result_items})

    except Exception as e:
        logger.error(f"下载任务失败 (job_id={job_id}): {e}", exc_info=True)
        set_download_progress(job_id, {
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
            "error": str(e),
        })


def start_download(
    job_id: int,
    url: str,
    out_dir: str,
    sessdata: str | None,
    playlist: bool,
    quality: str,
    workers: int,
    db_url: str | None,
) -> None:
    """启动后台下载线程"""
    t = threading.Thread(
        target=_download_worker,
        args=(job_id, url, out_dir, sessdata or "", playlist, quality, workers, db_url),
        daemon=True,
    )
    t.start()
