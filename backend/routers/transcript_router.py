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
from backend.config import settings


# 数据结构定义
class TranscriptItem(TypedDict, total=False):
    """转写记录项数据结构"""

    id: int  # 转写记录ID
    audio_path: str  # 音频文件路径
    video_path: Optional[str]  # 视频文件路径（可选）
    created_at: str  # 创建时间
    segment_count: int  # 句子片段数量


class ListTranscriptsResponse(TypedDict):
    """列出转写记录响应数据结构"""

    total: int  # 总数量
    items: List[TranscriptItem]  # 转写记录列表


class TranscriptSegment(TypedDict, total=False):
    """转写句子片段数据结构"""

    index: int  # 句子索引
    spk_id: Optional[str]  # 说话人ID
    sentence: str  # 句子文本
    start_time: float  # 开始时间（秒）
    end_time: float  # 结束时间（秒）


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
    summaries: Optional[List[Dict[str, Any]]]  # 总结列表
    translations: Optional[Dict[str, List[Dict[str, Any]]]]  # 翻译结果字典


class DeleteTranscriptResponse(TypedDict):
    """删除转写记录响应数据结构"""

    success: bool  # 是否成功
    message: str  # 响应消息
    transcript_id: int  # 转写记录ID


router = APIRouter(tags=["transcripts"])


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
