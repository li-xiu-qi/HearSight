# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.db.transcript_crud import (
    clear_chat_messages,
    get_chat_messages,
    get_summaries,
    save_chat_messages,
    save_summaries,
)
from backend.text_process.chat_with_segment import chat_with_segments
from backend.text_process.summarize import summarize_segments
from config import settings

# 数据结构定义
class Segment(TypedDict):
    """句子片段数据结构"""
    start: float  # 开始时间（秒）
    end: float  # 结束时间（秒）
    text: str  # 句子文本


class SummaryItem(TypedDict):
    """总结项数据结构"""
    title: str  # 总结标题
    content: str  # 总结内容


class SummarizeRequest(TypedDict, total=False):
    """总结请求数据结构"""
    segments: List[Segment]  # 句子片段列表
    api_key: str  # OpenAI API密钥
    base_url: str  # OpenAI API基础URL
    model: str  # 使用的模型


class SummarizeResponse(TypedDict):
    """总结响应数据结构"""
    summaries: List[SummaryItem]  # 总结项列表


class ChatRequest(TypedDict, total=False):
    """聊天请求数据结构"""
    segments: List[Segment]  # 句子片段列表
    question: str  # 问题内容
    api_key: str  # OpenAI API密钥
    base_url: str  # OpenAI API基础URL
    model: str  # 使用的模型


class ChatResponse(TypedDict):
    """聊天响应数据结构"""
    answer: str  # 回答内容


class SaveSummariesRequest(TypedDict):
    """保存总结请求数据结构"""
    summaries: List[SummaryItem]  # 总结项列表


class SaveSummariesResponse(TypedDict):
    """保存总结响应数据结构"""
    success: bool  # 是否成功
    message: str  # 响应消息
    saved: bool  # 是否已保存
    transcript_id: int  # 转录ID


class GetSummariesResponse(TypedDict):
    """获取总结响应数据结构"""
    summaries: Optional[List[SummaryItem]]  # 总结项列表，可能为None
    has_summaries: bool  # 是否有总结


class ChatMessage(TypedDict):
    """聊天消息数据结构"""
    role: str  # 消息角色 (user/assistant)
    content: str  # 消息内容
    timestamp: Optional[str]  # 时间戳


class SaveChatMessagesRequest(TypedDict):
    """保存聊天消息请求数据结构"""
    messages: List[ChatMessage]  # 聊天消息列表


class SaveChatMessagesResponse(TypedDict):
    """保存聊天消息响应数据结构"""
    success: bool  # 是否成功
    message: str  # 响应消息
    transcript_id: int  # 转录ID


class GetChatMessagesResponse(TypedDict):
    """获取聊天消息响应数据结构"""
    messages: Optional[List[ChatMessage]]  # 聊天消息列表，可能为None
    has_messages: bool  # 是否有消息


class ClearChatMessagesResponse(TypedDict):
    """清空聊天消息响应数据结构"""
    success: bool  # 是否成功
    message: str  # 响应消息
    transcript_id: int  # 转录ID


router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/summarize")
def api_summarize(payload: SummarizeRequest, request: Request) -> SummarizeResponse:
    """基于句级片段一次性生成总结。

        请求 body 字段：
            - segments: List[Segment] （必需）
            - api_key/base_url/model: 可选（若未提供则从 config 或环境变量读取）

    返回：{"summaries": List[SummaryItem]}
    """
    segments = payload.get("segments")
    if not segments or not isinstance(segments, list):
        raise HTTPException(status_code=400, detail="segments (list) is required")

    # 优先使用请求体中的配置；其次使用配置或环境变量
    api_key = (
        payload.get("api_key")
        or settings.openai_api_key
        or os.environ.get("OPENAI_API_KEY")
    )
    base_url = (
        payload.get("base_url")
        or settings.openai_base_url
        or os.environ.get("OPENAI_BASE_URL")
    )
    model = (
        payload.get("model")
        or settings.openai_chat_model
        or os.environ.get("OPENAI_CHAT_MODEL")
    )

    if not api_key or not base_url or not model:
        raise HTTPException(
            status_code=400,
            detail="chat api_key, base_url and model are required (either in payload or config/env)",
        )

    # 从配置或环境读取 CHAT_MAX_WINDOWS（优先级：config -> 环境变量 -> 默认 1000000）
    chat_max = settings.chat_max_windows or int(
        os.environ.get("CHAT_MAX_WINDOWS") or 1000000
    )

    try:
        summaries = summarize_segments(
            segments=segments,
            api_key=api_key,
            base_url=base_url,
            model=model,
            chat_max_windows=chat_max,
            max_tokens=4096,
        )
    except ValueError as e:
        # 例如 token 超限等可预期的错误，返回 400
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 其他未知错误返回 500
        raise HTTPException(status_code=500, detail=f"summarization failed: {e}")

    # 返回直接的 list[SummaryItem] 以简化前端处理
    return {"summaries": summaries}


@router.post("/chat")
def api_chat_with_segments(payload: ChatRequest, request: Request) -> ChatResponse:
    """基于分句内容进行问答。

    请求 body 字段：
        - segments: List[Segment] （必需）
        - question: str （必需）
        - api_key/base_url/model: 可选（若未提供则从 config 或环境变量读取）

    返回：{"answer": str}
    """
    segments = payload.get("segments")
    question = payload.get("question")

    if not segments or not isinstance(segments, list):
        raise HTTPException(status_code=400, detail="segments (list) is required")

    if not question or not isinstance(question, str):
        raise HTTPException(status_code=400, detail="question (string) is required")

    # 优先使用请求体中的配置；其次使用配置或环境变量
    api_key = (
        payload.get("api_key")
        or settings.openai_api_key
        or os.environ.get("OPENAI_API_KEY")
    )
    base_url = (
        payload.get("base_url")
        or settings.openai_base_url
        or os.environ.get("OPENAI_BASE_URL")
    )
    model = (
        payload.get("model")
        or settings.openai_chat_model
        or os.environ.get("OPENAI_CHAT_MODEL")
    )

    if not api_key or not base_url or not model:
        raise HTTPException(
            status_code=400,
            detail="chat api_key, base_url and model are required (either in payload or config/env)",
        )

    # 从配置或环境读取 CHAT_MAX_WINDOWS（优先级：config -> 环境变量 -> 默认 1000000）
    chat_max = settings.chat_max_windows or int(
        os.environ.get("CHAT_MAX_WINDOWS") or 1000000
    )

    try:
        answer = chat_with_segments(
            segments=segments,
            question=question,
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
        raise HTTPException(status_code=500, detail=f"chat failed: {e}")

    return {"answer": answer}


class SaveSummariesRequest(BaseModel):
    """保存总结的请求体"""

    transcript_id: int
    summaries: list


@router.post("/transcripts/{transcript_id}/summaries")
def api_save_summaries(
    transcript_id: int, payload: SaveSummariesRequest, request: Request
) -> SaveSummariesResponse:
    """保存生成的总结到数据库。

    请求 body 字段：
        - summaries: List[Dict] （必需）总结内容

    返回：{"success": bool, "message": str, "saved": bool}
    """
    db_url = request.app.state.db_url
    summaries = payload.get("summaries")

    if not summaries or not isinstance(summaries, list):
        raise HTTPException(status_code=400, detail="summaries (list) is required")

    try:
        success = save_summaries(db_url, transcript_id, summaries)
        if success:
            return {
                "success": True,
                "message": "总结已保存",
                "saved": True,
                "transcript_id": transcript_id,
            }
        else:
            raise HTTPException(
                status_code=404, detail=f"Transcript {transcript_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save summaries: {str(e)}"
        )


@router.get("/transcripts/{transcript_id}/summaries")
def api_get_summaries(transcript_id: int, request: Request) -> GetSummariesResponse:
    """获取已保存的总结。

    返回：{"summaries": List[Dict] | null, "has_summaries": bool}
    """
    db_url = request.app.state.db_url

    try:
        summaries = get_summaries(db_url, transcript_id)
        return {
            "summaries": summaries,
            "has_summaries": summaries is not None and len(summaries) > 0,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get summaries: {str(e)}"
        )


@router.post("/transcripts/{transcript_id}/chat-messages")
def api_save_chat_messages(
    transcript_id: int, payload: SaveChatMessagesRequest, request: Request
) -> SaveChatMessagesResponse:
    """保存chat消息到数据库。

    请求 body 字段：
        - messages: List[Dict] （必需）chat消息列表

    返回：{"success": bool, "message": str}
    """
    db_url = request.app.state.db_url
    messages = payload.get("messages")

    if not messages or not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="messages (list) is required")

    try:
        success = save_chat_messages(db_url, transcript_id, messages)
        if success:
            return {
                "success": True,
                "message": "chat消息已保存",
                "transcript_id": transcript_id,
            }
        else:
            raise HTTPException(
                status_code=404, detail=f"Transcript {transcript_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save chat messages: {str(e)}"
        )


@router.get("/transcripts/{transcript_id}/chat-messages")
def api_get_chat_messages(transcript_id: int, request: Request) -> GetChatMessagesResponse:
    """获取已保存的chat消息。

    返回：{"messages": List[Dict] | null, "has_messages": bool}
    """
    db_url = request.app.state.db_url

    try:
        messages = get_chat_messages(db_url, transcript_id)
        return {
            "messages": messages,
            "has_messages": messages is not None and len(messages) > 0,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get chat messages: {str(e)}"
        )


@router.delete("/transcripts/{transcript_id}/chat-messages")
def api_clear_chat_messages(transcript_id: int, request: Request) -> ClearChatMessagesResponse:
    """清空chat消息。

    返回：{"success": bool, "message": str}
    """
    db_url = request.app.state.db_url

    try:
        success = clear_chat_messages(db_url, transcript_id)
        if success:
            return {
                "success": True,
                "message": "chat消息已清空",
                "transcript_id": transcript_id,
            }
        else:
            raise HTTPException(
                status_code=404, detail=f"Transcript {transcript_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to clear chat messages: {str(e)}"
        )
