from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.db.pg_store import get_translations
from backend.services.transcript_service import (
    delete_transcript_async,
    get_transcript_async,
    list_transcripts_async,
)
from backend.services.translate_service import (
    get_translate_progress,
    start_translate_task,
)
from config import settings


class TranslateRequest(BaseModel):
    target_language: str = "zh"
    confirmed: bool = True
    max_tokens: int = 4096
    source_lang_name: Optional[str] = None
    target_lang_name: Optional[str] = None
    force_retranslate: bool = False


router = APIRouter(prefix="/api", tags=["transcripts"])


@router.get("/transcripts")
async def api_list_transcripts(
    request: Request, limit: int = 50, offset: int = 0
) -> Dict[str, Any]:
    """列出已转写的媒体列表（按id倒序）。
    Query:
      - limit: 返回数量（默认50）
      - offset: 偏移量（默认0）
    返回: { total, items: [{id, media_path, created_at, segment_count}] }
    """
    db_url = request.app.state.db_url
    return await list_transcripts_async(db_url, limit=limit, offset=offset)


@router.get("/transcripts/{transcript_id}")
async def api_get_transcript(transcript_id: int, request: Request) -> Dict[str, Any]:
    """获取指定转写记录的详情（包含 segments）。"""
    db_url = request.app.state.db_url
    data = await get_transcript_async(db_url, transcript_id)
    if not data:
        raise HTTPException(
            status_code=404, detail=f"transcript not found: {transcript_id}"
        )
    return data


@router.delete("/transcripts/{transcript_id}")
async def api_delete_transcript_complete(
    transcript_id: int, request: Request
) -> Dict[str, Any]:
    """删除指定的转写记录及其对应的视频文件。
    该操作会同时删除视频文件和数据库记录，不可恢复。
    """
    db_url = request.app.state.db_url
    static_dir: Path = request.app.state.static_dir

    result = await delete_transcript_async(db_url, transcript_id, static_dir)
    if not result:
        raise HTTPException(status_code=404, detail="转写记录不存在或已被删除")
    return result


@router.post("/transcripts/{transcript_id}/translate")
async def api_translate(
    transcript_id: int, request: Request, body: TranslateRequest
) -> Dict[str, Any]:
    """翻译转写内容。后台异步翻译，使用轮询查询进度。

    请求体: {
        "target_language": "zh" | "en",
        "confirmed": bool
    }

    返回: { "status": "started", "transcript_id": int }
    """
    db_url = request.app.state.db_url

    api_key = settings.openai_api_key
    base_url = settings.openai_base_url
    model = settings.openai_chat_model

    if not all([api_key, base_url, model]):
        logging.error("LLM 配置缺失")
        raise HTTPException(status_code=500, detail="LLM configuration is missing")

    data = await get_transcript_async(db_url, transcript_id)
    if not data:
        raise HTTPException(
            status_code=404, detail=f"transcript not found: {transcript_id}"
        )

    segments = data.get("segments", [])
    if not segments:
        raise HTTPException(status_code=400, detail="No segments to translate")

    return await start_translate_task(
        transcript_id,
        segments,
        body.target_language,
        body.max_tokens,
        api_key,
        base_url,
        model,
        body.source_lang_name or "",
        body.target_lang_name or "",
        db_url,
        force_retranslate=body.force_retranslate,
    )


@router.get("/transcripts/{transcript_id}/translate-progress")
async def api_get_translate_progress(
    transcript_id: int, request: Request
) -> Dict[str, Any]:
    """获取翻译进度。

    返回: {
        "status": "translating" | "completed" | "error",
        "progress": 0-100,
        "translated_count": int,
        "total_count": int,
        "message": str
    }
    """
    return get_translate_progress(transcript_id)


@router.get("/transcripts/{transcript_id}/translations")
async def api_get_translations(transcript_id: int, request: Request) -> Dict[str, Any]:
    """获取已保存的翻译结果。

    返回: {
        "translations": Dict[str, List] | null,
        "has_translations": bool
    }
    """
    db_url = request.app.state.db_url

    try:
        translations = get_translations(db_url, transcript_id)
        return {
            "translations": translations,
            "has_translations": translations is not None and len(translations) > 0,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get translations: {str(e)}"
        )
