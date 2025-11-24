# -*- coding: utf-8 -*-
"""
聊天服务模块

整合聊天逻辑和知识库服务。
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)
import os
from typing import List, Dict, Optional

# 动态导入配置
try:
    from backend.config import settings
    from backend.schemas import Segment
except ImportError:
    # 如果backend模块找不到，尝试添加路径
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if backend_dir not in os.sys.path:
        os.sys.path.insert(0, backend_dir)
    from backend.config import settings
    from backend.schemas import Segment

from backend.services.knowledge_base_service import knowledge_base
from backend.utils.token_utils.calculate_tokens import OpenAITokenCalculator
from backend.services.chat_prompt_service import ChatPromptService
from backend.services.chat_knowledge_service import ChatKnowledgeService
from backend.startup import get_llm_router


class ChatService(ChatPromptService, ChatKnowledgeService):
    """聊天服务类"""

    def __init__(self):
        """初始化聊天服务"""
        pass

    def chat_with_transcripts_stream(
        self,
        question: str,
        transcript_ids: List[int],
        chat_max_windows: int = 1_000_000,
        stream_callback: Optional[callable] = None,
    ):
        """
        基于多个转录内容进行智能问答（流式版本）。

        Args:
            question: 用户问题
            transcript_ids: 转录ID列表（支持单视频或多视频）
            chat_max_windows: 最大token限制
            stream_callback: 流式回调函数，如果提供则使用回调，否则使用yield

        生成器函数，逐个返回带有标记的文本片段。
        标记格式：[chunk]文本内容[/chunk]
        """
        # 对每个transcript_id执行检索
        all_segments = []
        video_info = []

        for transcript_id in transcript_ids:
            relevant_segments, filename = self._perform_knowledge_retrieval(question, transcript_id)
            if relevant_segments:
                all_segments.extend(relevant_segments)
                if filename:
                    video_info.append({"filename": filename, "transcript_id": transcript_id})

        # 如果没有检索到内容，报错
        if not all_segments:
            error_msg = "[error]No relevant content found in the selected transcripts[/error]"
            if stream_callback:
                stream_callback(error_msg)
            else:
                yield error_msg
            return

        # 按index排序确保内容连贯
        all_segments.sort(key=lambda s: s.get("index", 0))

        tokens = self._count_tokens_for_segments(all_segments)
        if tokens > chat_max_windows:
            error_msg = f"[error]Input tokens {tokens} exceed chat_max_windows {chat_max_windows}[/error]"
            if stream_callback:
                stream_callback(error_msg)
            else:
                yield error_msg
            return

        prompt = self._build_multi_video_prompt(all_segments, question, video_info)

        # 执行流式完成
        for item in self._perform_streaming_completion(
            prompt=prompt,
            stream_callback=stream_callback
        ):
            yield item

    def _perform_streaming_completion(
        self,
        prompt: str,
        stream_callback: Optional[callable] = None,
    ):
        """
        执行流式 LLM 完成的私有方法。

        Args:
            prompt: 提示词
            stream_callback: 流式回调函数

        Yields:
            流式响应片段
        """
        try:
            # 获取全局 Router
            router = get_llm_router()

            # 使用 Router 流式调用
            response = router.completion(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    # 用标记包装每个文本片段（用于yield模式）
                    chunk_msg = f"[chunk]{content}[/chunk]"
                    if stream_callback:
                        # 回调模式发送纯文本
                        stream_callback(content)
                    else:
                        yield chunk_msg

            # 发送结束标记
            done_msg = "[done][/done]"
            if stream_callback:
                # 回调模式不需要发送done标记，由调用方处理
                pass
            else:
                yield done_msg

        except Exception as e:
            error_msg = f"[error]{str(e)}[/error]"
            if stream_callback:
                stream_callback(error_msg)
            else:
                yield error_msg


# 全局实例
chat_service = ChatService()