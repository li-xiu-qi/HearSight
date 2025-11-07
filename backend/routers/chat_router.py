# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.db.pg_store import get_summaries, save_summaries
from backend.text_process.chat_with_segment import chat_with_segments
from backend.text_process.summarize import summarize_segments
from config import settings

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/summarize")
def api_summarize(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
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
def api_chat_with_segments(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
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
    transcript_id: int, payload: Dict[str, Any], request: Request
) -> Dict[str, Any]:
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
def api_get_summaries(transcript_id: int, request: Request) -> Dict[str, Any]:
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
