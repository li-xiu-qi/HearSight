# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request

from backend.text_process.summarize import summarize_segments
from backend.text_process.chat_with_segment import chat_with_segments
from config import get_config
import os

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

    # 优先使用请求体中的配置；其次使用配置文件（config）或环境变量
    cfg = get_config()
    api_key = payload.get("api_key") or cfg.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
    base_url = payload.get("base_url") or cfg.OPENAI_BASE_URL or os.environ.get("OPENAI_BASE_URL")
    model = payload.get("model") or cfg.OPENAI_CHAT_MODEL or os.environ.get("OPENAI_CHAT_MODEL")

    if not api_key or not base_url or not model:
        raise HTTPException(status_code=400, detail="chat api_key, base_url and model are required (either in payload or config/env)")

    # 从配置或环境读取 CHAT_MAX_WINDOWS（优先级：config -> 环境变量 -> 默认 1000000）
    chat_max = None
    if hasattr(cfg, 'CHAT_MAX_WINDOWS') and cfg.CHAT_MAX_WINDOWS:
        try:
            chat_max = int(cfg.CHAT_MAX_WINDOWS)
        except Exception:
            chat_max = None
    if chat_max is None:
        try:
            chat_max = int(os.environ.get('CHAT_MAX_WINDOWS') or os.environ.get('CHAT_MAX_WINDOWS'.upper()) or '1000000')
        except Exception:
            chat_max = 1000000

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

    # 优先使用请求体中的配置；其次使用配置文件（config）或环境变量
    cfg = get_config()
    api_key = payload.get("api_key") or cfg.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
    base_url = payload.get("base_url") or cfg.OPENAI_BASE_URL or os.environ.get("OPENAI_BASE_URL")
    model = payload.get("model") or cfg.OPENAI_CHAT_MODEL or os.environ.get("OPENAI_CHAT_MODEL")

    if not api_key or not base_url or not model:
        raise HTTPException(status_code=400, detail="chat api_key, base_url and model are required (either in payload or config/env)")

    # 从配置或环境读取 CHAT_MAX_WINDOWS（优先级：config -> 环境变量 -> 默认 1000000）
    chat_max = None
    if hasattr(cfg, 'CHAT_MAX_WINDOWS') and cfg.CHAT_MAX_WINDOWS:
        try:
            chat_max = int(cfg.CHAT_MAX_WINDOWS)
        except Exception:
            chat_max = None
    if chat_max is None:
        try:
            chat_max = int(os.environ.get('CHAT_MAX_WINDOWS') or os.environ.get('CHAT_MAX_WINDOWS'.upper()) or '1000000')
        except Exception:
            chat_max = 1000000

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