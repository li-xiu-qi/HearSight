# -*- coding: utf-8 -*-
"""聊天对话相关的路由"""

import asyncio
import json
import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.services.chat_service import chat_service
from backend.db.job_store import create_job
from .models import ChatRequest, ChatResponse, ChatTaskResponse


router = APIRouter()


@router.post("/chat/stream")
def api_chat_with_transcripts_stream(payload: ChatRequest, request: Request):
    """基于数据库转录内容进行问答（流式响应）。

    请求 body 字段：
        - question: str （必需）
        - api_key/base_url/model: 可选（若未提供则从 config 或环境变量读取）
        - transcript_ids: List[int] （必需，转录ID列表，支持单视频或多视频）

    返回：流式响应，带有标记的文本片段
    """

    question = payload.get("question")
    transcript_ids = payload.get("transcript_ids")

    if not transcript_ids or not isinstance(transcript_ids, list) or len(transcript_ids) == 0:
        raise HTTPException(status_code=400, detail="transcript_ids (list) is required and cannot be empty")

    if not question or not isinstance(question, str):
        raise HTTPException(status_code=400, detail="question (string) is required")


    # 从配置或环境读取 CHAT_MAX_WINDOWS（优先级：环境变量 -> 默认 1000000）
    chat_max = int(
        os.environ.get("CHAT_MAX_WINDOWS") or 1000000
    )

    try:
        # 根据transcript_ids的数量决定使用单视频还是多视频逻辑
        if len(transcript_ids) > 1:
            # 多视频流式chat
            generator = chat_service.chat_with_multiple_transcripts_stream(
                question=question,
                transcript_ids=transcript_ids,
                chat_max_windows=chat_max,
            )
        elif len(transcript_ids) == 1:
            # 单视频流式chat
            generator = chat_service.chat_with_segments_stream(
                question=question,
                transcript_id=transcript_ids[0],
                chat_max_windows=chat_max,
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid transcript_ids")

        return StreamingResponse(
            generator,
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start streaming chat: {e}")


@router.post("/chat/streaming")
def api_create_streaming_chat_task(payload: ChatRequest, request: Request) -> ChatTaskResponse:
    """创建流式聊天任务（SSE方式）。

    请求 body 字段：
        - question: str （必需）
        - api_key/base_url/model: 可选（若未提供则从 config 或环境变量读取）
        - transcript_ids: List[int] （必需，转录ID列表，支持单视频或多视频）

    返回：{"task_id": int, "status": "pending"}
    """
    question = payload.get("question")
    transcript_ids = payload.get("transcript_ids")

    if not transcript_ids or not isinstance(transcript_ids, list) or len(transcript_ids) == 0:
        raise HTTPException(status_code=400, detail="transcript_ids (list) is required and cannot be empty")

    if not question or not isinstance(question, str):
        raise HTTPException(status_code=400, detail="question (string) is required")

    api_key = payload.get("api_key")
    base_url = payload.get("base_url") 
    model = payload.get("model")

    # 从配置或环境读取 CHAT_MAX_WINDOWS（优先级：环境变量 -> 默认 1000000）
    chat_max = int(
        os.environ.get("CHAT_MAX_WINDOWS") or 1000000
    )

    db_url = request.app.state.db_url

    try:
        # 创建流式聊天任务
        job_id = create_job(db_url, f"streaming_chat://{question[:50]}...")

        # 提交异步流式任务
        from backend.queues.tasks.process_job_task import process_streaming_chat_task
        task = process_streaming_chat_task.delay(
            job_id=job_id,
            question=question,
            transcript_ids=transcript_ids,
            chat_max_windows=chat_max,
            db_url=db_url,
        )

        # 更新任务的 celery_task_id
        from backend.db.job_store import update_job_celery_task_id
        update_job_celery_task_id(db_url, job_id, task.id)

        return {"task_id": job_id, "status": "pending"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create streaming chat task: {e}")


@router.get("/chat/{task_id}/stream")
async def api_stream_chat_response(task_id: int, request: Request):
    """流式聊天响应（SSE方式）。

    返回SSE流，实时推送聊天内容块。
    """
    from backend.routers.progress_router import redis_client

    pubsub = redis_client.pubsub()
    pubsub.subscribe(f"chat_stream:{task_id}")

    async def event_generator():
        try:
            while True:
                message = pubsub.get_message(ignore_subscribe_messages=True)
                if message and message.get('type') == 'message':
                    data = message.get('data')
                    # 确保data是字符串格式的JSON
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                    # 验证JSON格式
                    try:
                        json.loads(data)  # 验证是否为有效JSON
                        print(f"[SSE] 发送数据: {data}")
                        yield f"data: {data}\n\n"
                    except json.JSONDecodeError as e:
                        print(f"[SSE] 无效JSON数据: {data}, 错误: {e}")
                        continue
                await asyncio.sleep(0.1)
        finally:
            try:
                pubsub.unsubscribe(f"chat_stream:{task_id}")
            except Exception:
                pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )