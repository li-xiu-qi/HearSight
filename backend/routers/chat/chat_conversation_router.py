# -*- coding: utf-8 -*-
"""聊天对话相关的路由"""

import os
from fastapi import APIRouter, HTTPException, Request

from backend.services.chat_service import chat_service
from .models import ChatRequest, ChatResponse
from .utils import get_llm_config


router = APIRouter()


@router.post("/chat")
def api_chat_with_transcripts(payload: ChatRequest, request: Request) -> ChatResponse:
    """基于数据库转录内容进行问答。

    请求 body 字段：
        - question: str （必需）
        - api_key/base_url/model: 可选（若未提供则从 config 或环境变量读取）
        - transcript_ids: List[int] （必需，转录ID列表，支持单视频或多视频）

    返回：{"answer": str}
    """
    question = payload.get("question")
    transcript_ids = payload.get("transcript_ids")

    if not transcript_ids or not isinstance(transcript_ids, list) or len(transcript_ids) == 0:
        raise HTTPException(status_code=400, detail="transcript_ids (list) is required and cannot be empty")

    if not question or not isinstance(question, str):
        raise HTTPException(status_code=400, detail="question (string) is required")

    api_key, base_url, model = get_llm_config(payload)

    # 从配置或环境读取 CHAT_MAX_WINDOWS（优先级：环境变量 -> 默认 1000000）
    chat_max = int(
        os.environ.get("CHAT_MAX_WINDOWS") or 1000000
    )

    try:
        # 根据transcript_ids的数量决定使用单视频还是多视频逻辑
        if len(transcript_ids) > 1:
            # 多视频chat
            answer = chat_service.chat_with_multiple_transcripts(
                question=question,
                api_key=api_key,
                base_url=base_url,
                model=model,
                transcript_ids=transcript_ids,
                chat_max_windows=chat_max,
            )
        elif len(transcript_ids) == 1:
            # 单视频chat
            answer = chat_service.chat_with_segments(
                question=question,
                api_key=api_key,
                base_url=base_url,
                model=model,
                transcript_id=transcript_ids[0],
                chat_max_windows=chat_max,
            )
        else:
            # 不应该到达这里，因为transcript_ids至少有1个
            raise HTTPException(status_code=400, detail="Invalid transcript_ids")
    except ValueError as e:
        # 例如 token 超限等可预期的错误，返回 400
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 其他未知错误返回 500
        raise HTTPException(status_code=500, detail=f"chat failed: {e}")

    return {"answer": answer}