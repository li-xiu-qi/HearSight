# -*- coding: utf-8 -*-
"""聊天任务处理阶段"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from backend.services.chat_service import chat_service
from .progress_utils import update_task_progress, create_progress_info


def handle_streaming_chat_stage(
    question: str,
    transcript_ids: List[int],
    chat_max_windows: int,
    job_id: int,
    set_task_progress: Any,
    progress_redis_client: Any,
) -> Dict[str, Any]:
    """处理流式聊天任务阶段。

    Args:
        question: 用户问题
        transcript_ids: 转录ID列表
        chat_max_windows: 聊天最大窗口
        job_id: 任务ID
        set_task_progress: 进度更新函数
        progress_redis_client: Redis客户端

    Returns:
        聊天结果字典
    """
    logger = logging.getLogger(__name__)

    print(f"[DEBUG] handle_streaming_chat_stage 开始，job_id={job_id}, question={question}, transcript_ids={transcript_ids}")

    try:
        # 更新进度：开始流式聊天处理
        progress_info = create_progress_info(
            job_id, "in-progress", "chat", 10,
            message="正在启动流式聊天...",
        )
        update_task_progress(set_task_progress, progress_redis_client, job_id, progress_info)

        full_answer = ""

        def stream_callback(chunk: str):
            nonlocal full_answer
            
            print(f"[DEBUG] stream_callback 收到 chunk: {repr(chunk)}")
            
            # 检查是否是错误消息
            if chunk.startswith("[error]") and chunk.endswith("[/error]"):
                # 提取错误信息
                error_content = chunk[7:-8]  # 移除[error]和[/error]
                # 发送错误事件
                error_data = {"error": error_content}
                progress_redis_client.publish(f"chat_stream:{job_id}", json.dumps({
                    "event": "error",
                    "data": error_data
                }))
                # 更新进度为失败
                progress_info = create_progress_info(
                    job_id, "failed", "chat", 0,
                    message=f"流式聊天失败: {error_content}",
                    error=error_content,
                )
                update_task_progress(set_task_progress, progress_redis_client, job_id, progress_info)
                return
            
            full_answer += chunk

            # 发布SSE事件到Redis
            event_data = {
                "chunk": chunk,
                "type": "text"
            }
            progress_redis_client.publish(f"chat_stream:{job_id}", json.dumps(event_data))

            # 更新进度
            progress_info = create_progress_info(
                job_id, "in-progress", "chat", min(90, 10 + len(full_answer) // 10),
                message=f"正在生成回答... ({len(full_answer)} 字符)",
            )
            update_task_progress(set_task_progress, progress_redis_client, job_id, progress_info)

        # 根据transcript_ids的数量决定使用单视频还是多视频逻辑
        if len(transcript_ids) > 1:
            print(f"[DEBUG] 调用多视频 chat_service，transcript_ids={transcript_ids}")
            # 多视频流式chat
            generator = chat_service.chat_with_multiple_transcripts_stream(
                question=question,
                transcript_ids=transcript_ids,
                chat_max_windows=chat_max_windows,
                stream_callback=stream_callback
            )
        elif len(transcript_ids) == 1:
            print(f"[DEBUG] 调用单视频 chat_service，transcript_id={transcript_ids[0]}")
            # 单视频流式chat
            generator = chat_service.chat_with_segments_stream(
                question=question,
                transcript_id=transcript_ids[0],
                chat_max_windows=chat_max_windows,
                stream_callback=stream_callback
            )
        else:
            raise ValueError("Invalid transcript_ids")

        # 消费生成器以确保执行完成
        for _ in generator:
            pass

        print(f"[DEBUG] chat_service 调用完成，full_answer 长度: {len(full_answer)}")

        print(f"[DEBUG] 发送完成事件，final_answer={repr(full_answer)}")
        # 发送完成事件
        complete_data = {"final_answer": full_answer}
        progress_redis_client.publish(f"chat_stream:{job_id}", json.dumps({
            "event": "complete",
            "data": complete_data
        }))

        # 更新进度：完成
        progress_info = create_progress_info(
            job_id, "completed", "chat", 100,
            message="流式聊天完成",
        )
        update_task_progress(set_task_progress, progress_redis_client, job_id, progress_info)

        return {"answer": full_answer}

    except Exception as e:
        logger.error(f"Streaming chat stage failed for job {job_id}: {e}")

        # 发送错误事件
        error_data = {"error": str(e)}
        progress_redis_client.publish(f"chat_stream:{job_id}", json.dumps({
            "event": "error",
            "data": error_data
        }))

        update_task_progress(
            set_task_progress,
            progress_redis_client,
            job_id,
            create_progress_info(
                job_id, "failed", "chat", 0,
                message=f"流式聊天失败: {str(e)}",
                error=str(e),
            )
        )
        raise