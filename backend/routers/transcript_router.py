from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing_extensions import TypedDict

from backend.db.transcript_crud import get_translations
from backend.services.transcript_service import (delete_transcript_async,
                                                 get_transcript_async,
                                                 list_transcripts_async)
from backend.services.translate_service import (get_translate_progress,
                                                start_translate_task)
from config import settings


# 数据结构定义
class TranscriptItem(TypedDict, total=False):
    """转写记录项数据结构"""

    id: int  # 转写记录ID
    media_path: str  # 媒体文件路径
    created_at: str  # 创建时间
    segment_count: int  # 句子片段数量


class ListTranscriptsResponse(TypedDict):
    """列出转写记录响应数据结构"""

    total: int  # 总数量
    items: List[TranscriptItem]  # 转写记录列表


class TranscriptSegment(TypedDict):
    """转写句子片段数据结构"""

    start: float  # 开始时间（秒）
    end: float  # 结束时间（秒）
    text: str  # 句子文本


class TranscriptData(TypedDict, total=False):
    """转写记录详情数据结构。

    媒体类型来自数据库的 transcripts 表中的 media_type 字段。
    在转写记录创建时根据文件扩展名自动判断：
    - 音频扩展名（.m4a, .mp3, .wav, .flac, .aac, .ogg, .wma）-> 'audio'
    - 其他扩展名 -> 'video'
    """

    id: int  # 转写记录ID
    media_path: str  # 媒体文件路径
    created_at: str  # 创建时间
    segments: List[TranscriptSegment]  # 句子片段列表
    media_type: str  # 媒体类型（'audio' 或 'video'）


class DeleteTranscriptResponse(TypedDict):
    """删除转写记录响应数据结构"""

    success: bool  # 是否成功
    message: str  # 响应消息
    transcript_id: int  # 转写记录ID


class TranslateRequestData(TypedDict, total=False):
    """翻译请求数据结构"""

    target_language: str  # 目标语言
    confirmed: bool  # 是否确认
    max_tokens: int  # 最大token数
    source_lang_name: str  # 源语言名称
    target_lang_name: str  # 目标语言名称
    force_retranslate: bool  # 是否强制重新翻译


class StartTranslateResponse(TypedDict):
    """开始翻译响应数据结构"""

    status: str  # 状态
    transcript_id: int  # 转写记录ID


class TranslateProgressResponse(TypedDict):
    """翻译进度响应数据结构"""

    status: str  # 翻译状态
    progress: int  # 进度百分比
    translated_count: int  # 已翻译数量
    total_count: int  # 总数
    message: str  # 状态消息


class GetTranslationsResponse(TypedDict):
    """获取翻译结果响应数据结构"""

    translations: Optional[Dict[str, List[Any]]]  # 翻译结果字典
    has_translations: bool  # 是否有翻译结果


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
) -> ListTranscriptsResponse:
    """列出已转写的媒体列表（按id倒序）。
    Query:
      - limit: 返回数量（默认50）
      - offset: 偏移量（默认0）
    返回: { total, items: [{id, media_path, created_at, segment_count}] }
    """
    db_url = request.app.state.db_url
    return await list_transcripts_async(db_url, limit=limit, offset=offset)


@router.get("/transcripts/{transcript_id}")
async def api_get_transcript(transcript_id: int, request: Request) -> TranscriptData:
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
) -> DeleteTranscriptResponse:
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
) -> StartTranslateResponse:
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
) -> TranslateProgressResponse:
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
async def api_get_translations(
    transcript_id: int, request: Request
) -> GetTranslationsResponse:
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
