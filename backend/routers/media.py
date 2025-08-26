# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from backend.audio2text.asr_sentence_segments import process as asr_process
from backend.db.pg_store import (
    save_transcript,
    list_transcripts_meta,
    count_transcripts,
    get_transcript_by_id,
    create_job,
    get_job,
    list_jobs,
)
from backend.utils.vedio_utils.download_video.download_bilibili import download_bilibili
from backend.text_process.summarize import summarize_segments
from config import get_config
import os

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
    # 保存到数据库（使用 postgres dsn 或由 pg_store 从环境读取）
    db_url = request.app.state.db_url
    transcript_id = save_transcript(db_url, str(p.resolve()), segs)
    return {"segments": segs, "transcript_id": transcript_id}


@router.post("/summarize")
def api_summarize(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    """基于句级片段一次性生成总结。

        请求 body 字段：
            - segments: List[Segment] （必需）
            - api_key/base_url/model: 可选（若未提供则从 config 或环境变量读取）
            - 注意：不要通过 payload 传入 max_tokens，后端使用 CHAT_MAX_WINDOWS 配置控制上限

    返回：{"summaries": List[SummaryItem]}
    """
    segments = payload.get("segments")
    if not segments or not isinstance(segments, list):
        raise HTTPException(status_code=400, detail="segments (list) is required")

    # 优先使用请求体中的配置；其次使用配置文件（config）或环境变量
    cfg = get_config()
    api_key = payload.get("api_key") or cfg.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
    base_url = payload.get("base_url") or cfg.OPENAI_BASE_URL or os.environ.get("OPENAI_BASE_URL")
    model = payload.get("model") or cfg.OPENAI_CHAT_MODEL or os.environ.get("OPENAI_CHAT_MODEL")

    if not api_key or not base_url or not model:
        raise HTTPException(status_code=400, detail="chat api_key, base_url and model are required (either in payload or config/env)")

    # 从配置或环境读取 CHAT_MAX_WINDOWS（优先级：config -> 环境变量 -> 默认 1000000）
    chat_max = None
    if getattr(cfg, 'CHAT_MAX_WINDOWS', None):
        try:
            chat_max = int(cfg.CHAT_MAX_WINDOWS)
        except Exception:
            chat_max = None
    if chat_max is None:
        chat_max = int(os.environ.get('CHAT_MAX_WINDOWS') or os.environ.get('CHAT_MAX_WINDOWS'.upper()) or 1000000)


    try:
        summaries = summarize_segments(
            segments=segments,
            api_key=api_key,
            base_url=base_url,
            model=model,
            chat_max_windows=chat_max,
        )
    except ValueError as e:
        # 例如 token 超限等可预期的错误，返回 400
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 其他未知错误返回 500
        raise HTTPException(status_code=500, detail=f"summarization failed: {e}")

    # 返回直接的 list[SummaryItem] 以简化前端处理
    return summaries


@router.get("/transcripts")
def api_list_transcripts(request: Request, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """列出已转写的媒体列表（按id倒序）。
    Query:
      - limit: 返回数量（默认50）
      - offset: 偏移量（默认0）
    返回: { total, items: [{id, media_path, created_at, segment_count}] }
    """
    db_url = request.app.state.db_url
    total = count_transcripts(db_url)
    items = list_transcripts_meta(db_url, limit=limit, offset=offset)
    return {"total": total, "items": items}


@router.get("/transcripts/{transcript_id}")
def api_get_transcript(transcript_id: int, request: Request) -> Dict[str, Any]:
    """获取指定转写记录的详情（包含 segments）。"""
    db_url = request.app.state.db_url
    data = get_transcript_by_id(db_url, transcript_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"transcript not found: {transcript_id}")
    return data


@router.post("/jobs")
def api_create_job(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    db_url = request.app.state.db_url
    job_id = create_job(db_url, str(url))
    return {"job_id": job_id}


@router.get("/jobs/{job_id}")
def api_get_job(job_id: int, request: Request) -> Dict[str, Any]:
    db_url = request.app.state.db_url
    data = get_job(db_url, int(job_id))
    if not data:
        raise HTTPException(status_code=404, detail=f"job not found: {job_id}")
    return data


@router.get("/jobs")
def api_list_jobs(request: Request, status: str | None = None, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """列出任务队列，支持按状态筛选（pending/running/success/failed）。
    返回: { items: [{id, url, status, created_at, started_at, finished_at, result, error}] }
    """
    db_url = request.app.state.db_url
    items = list_jobs(db_url, status=status, limit=limit, offset=offset)
    return {"items": items}
