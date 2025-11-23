# -*- coding: utf-8 -*-
"""聊天对话相关的路由"""

import os
from fastapi import APIRouter, HTTPException, Request

from backend.services.chat_service import chat_service
from .models import ChatRequest, ChatResponse
from .utils import get_llm_config


router = APIRouter()


@router.post("/chat")
def api_chat_with_segments(payload: ChatRequest, request: Request) -> ChatResponse:
    """基于分句内容进行问答。

    请求 body 字段：
        - segments: List[Segment] （必需）
        - question: str （必需）
        - api_key/base_url/model: 可选（若未提供则从 config 或环境变量读取）
        - transcript_ids: List[int] （可选，转录ID列表，支持单视频或多视频）

    返回：{"answer": str}
    """
    segments = payload.get("segments")
    question = payload.get("question")
    transcript_ids = payload.get("transcript_ids")

    if not segments or not isinstance(segments, list):
        raise HTTPException(status_code=400, detail="segments (list) is required")

    if not question or not isinstance(question, str):
        raise HTTPException(status_code=400, detail="question (string) is required")

    api_key, base_url, model = get_llm_config(payload)

    # 从配置或环境读取 CHAT_MAX_WINDOWS（优先级：环境变量 -> 默认 1000000）
    chat_max = int(
        os.environ.get("CHAT_MAX_WINDOWS") or 1000000
    )

    try:
        # 根据transcript_ids的数量决定使用单视频还是多视频逻辑
        if transcript_ids and len(transcript_ids) > 1:
            # 多视频chat
            answer = chat_service.chat_with_multiple_transcripts(
                segments=segments,
                question=question,
                api_key=api_key,
                base_url=base_url,
                model=model,
                chat_max_windows=chat_max,
                transcript_ids=transcript_ids,
            )
        elif transcript_ids and len(transcript_ids) == 1:
            # 单视频chat
            answer = chat_service.chat_with_segments(
                segments=segments,
                question=question,
                api_key=api_key,
                base_url=base_url,
                model=model,
                chat_max_windows=chat_max,
                transcript_id=transcript_ids[0],
            )
        else:
            # 未指定视频，在全部范围内进行检索
            from backend.db.transcript_crud import get_all_transcript_ids
            db_url = None  # connect_db 会使用环境变量
            all_transcript_ids = get_all_transcript_ids(db_url)
            if all_transcript_ids:
                answer = chat_service.chat_with_multiple_transcripts(
                    segments=segments,
                    question=question,
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    chat_max_windows=chat_max,
                    transcript_ids=all_transcript_ids,
                )
            else:
                # 如果没有可用的转录稿，直接基于提供的segments
                answer = chat_service.chat_with_segments(
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