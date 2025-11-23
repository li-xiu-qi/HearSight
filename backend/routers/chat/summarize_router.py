# -*- coding: utf-8 -*-
"""总结相关的路由"""

import os
from fastapi import APIRouter, HTTPException, Request

from backend.text_process.summarize import summarize_segments
from .models import SummarizeRequest, SummarizeResponse


router = APIRouter()


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

    # 从配置或环境读取 CHAT_MAX_WINDOWS（优先级：环境变量 -> 默认 1000000）
    chat_max = int(
        os.environ.get("CHAT_MAX_WINDOWS") or 1000000
    )

    try:
        summaries = summarize_segments(
            segments=segments,
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