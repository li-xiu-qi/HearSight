# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from backend.download_video.download_bilibili import download_bilibili
from backend.audio2text.asr_sentence_segments import process as asr_process
from backend.db.sqlite_store import (
    save_transcript,
    list_transcripts_meta,
    count_transcripts,
    get_transcript_by_id,
    create_job,
    get_job,
    list_jobs,
)

router = APIRouter(prefix="/api", tags=["media"])


@router.post("/download")
def api_download(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    static_dir: Path = request.app.state.static_dir
    out_dir = payload.get("out_dir") or str(static_dir)
    sessdata = payload.get("sessdata")
    playlist = bool(payload.get("playlist", False))
    quality = payload.get("quality", "best")
    workers = int(payload.get("workers", 16))

    files = download_bilibili(
        url=url,
        out_dir=out_dir,
        sessdata=sessdata,
        playlist=playlist,
        quality=quality,
        workers=workers,
        use_nopart=True,
        simple_filename=True,
    )

    items: List[Dict[str, Any]] = []
    for fp in files:
        p = Path(fp)
        # 只暴露静态访问路径
        items.append({
            "path": str(p.resolve()),
            "basename": p.name,
            "static_url": f"/static/{p.name}",
        })

    return {"items": items}


@router.post("/asr/segments")
def api_asr_segments(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    audio_path = payload.get("audio_path")
    if not audio_path:
        raise HTTPException(status_code=400, detail="audio_path is required")

    p = Path(audio_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"audio not found: {audio_path}")

    segs = asr_process(str(p))
    # 保存到数据库
    db_path: Path = request.app.state.db_path
    transcript_id = save_transcript(db_path, str(p.resolve()), segs)
    return {"segments": segs, "transcript_id": transcript_id}


@router.get("/transcripts")
def api_list_transcripts(request: Request, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """列出已转写的媒体列表（按id倒序）。
    Query:
      - limit: 返回数量（默认50）
      - offset: 偏移量（默认0）
    返回: { total, items: [{id, media_path, created_at, segment_count}] }
    """
    db_path: Path = request.app.state.db_path
    total = count_transcripts(db_path)
    items = list_transcripts_meta(db_path, limit=limit, offset=offset)
    return {"total": total, "items": items}


@router.get("/transcripts/{transcript_id}")
def api_get_transcript(transcript_id: int, request: Request) -> Dict[str, Any]:
    """获取指定转写记录的详情（包含 segments）。"""
    db_path: Path = request.app.state.db_path
    data = get_transcript_by_id(db_path, transcript_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"transcript not found: {transcript_id}")
    return data


@router.post("/jobs")
def api_create_job(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    db_path: Path = request.app.state.db_path
    job_id = create_job(db_path, str(url))
    return {"job_id": job_id}


@router.get("/jobs/{job_id}")
def api_get_job(job_id: int, request: Request) -> Dict[str, Any]:
    db_path: Path = request.app.state.db_path
    data = get_job(db_path, int(job_id))
    if not data:
        raise HTTPException(status_code=404, detail=f"job not found: {job_id}")
    return data


@router.get("/jobs")
def api_list_jobs(request: Request, status: str | None = None, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """列出任务队列，支持按状态筛选（pending/running/success/failed）。
    返回: { items: [{id, url, status, created_at, started_at, finished_at, result, error}] }
    """
    db_path: Path = request.app.state.db_path
    items = list_jobs(db_path, status=status, limit=limit, offset=offset)
    return {"items": items}
