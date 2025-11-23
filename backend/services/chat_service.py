# -*- coding: utf-8 -*-
"""
聊天服务模块

整合聊天逻辑和知识库服务。
"""

from __future__ import annotations

import json
import os
from typing import List, Dict, Optional

import litellm

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


class ChatService(ChatPromptService, ChatKnowledgeService):
    """聊天服务类"""

    def __init__(self):
        """初始化聊天服务"""
        pass

    def chat_with_segments(
        self,
        question: str,
        api_key: str,
        base_url: str,
        model: str,
        transcript_id: int,
        chat_max_windows: int = 1_000_000,
    ) -> str:
        """
        基于数据库转录内容进行智能问答。

        根据内容长度智能选择使用完整内容或检索内容。

        参数：
        - question: 用户问题
        - api_key: LLM API密钥
        - base_url: LLM API基础URL
        - model: LLM模型名称
        - chat_max_windows: 最大token限制
        - transcript_id: 转录ID

        返回：
        - LLM生成的回答
        """
        is_from_retrieval = False
        filename = None

        # 从数据库获取完整转录稿
        from backend.db.transcript_crud import get_transcript_by_id
        db_url = None  # connect_db 会使用环境变量
        full_transcript = get_transcript_by_id(db_url, transcript_id)
        if not full_transcript or "segments" not in full_transcript:
            raise ValueError(f"Transcript {transcript_id} not found or has no segments")

        full_segments = full_transcript["segments"]
        full_tokens = self._count_tokens_for_segments(full_segments)
        threshold = settings.llm_context_length or 100000
        
        # 获取文件名
        import os
        video_path = full_transcript.get("video_path")
        audio_path = full_transcript.get("audio_path")
        if video_path:
            filename = os.path.basename(video_path)
        elif audio_path:
            filename = os.path.basename(audio_path)
        
        if full_tokens <= threshold:
            # 直接使用完整转录稿
            segments = full_segments
            tokens = full_tokens
        else:
            # 使用知识库检索相关segments
            is_from_retrieval = True
            segments, filename = self._perform_knowledge_retrieval(question, transcript_id)
            tokens = self._count_tokens_for_segments(segments)

        if tokens > chat_max_windows:
            raise ValueError(
                f"input tokens {tokens} exceed chat_max_windows {chat_max_windows}"
            )

        prompt = self._build_prompt(segments, question, is_from_retrieval=is_from_retrieval, filename=filename)

        # 设置 LiteLLM 环境变量
        os.environ["OPENAI_API_KEY"] = api_key
        if base_url:
            os.environ["OPENAI_API_BASE"] = base_url

        # 使用 LiteLLM 调用
        response = litellm.completion(
            model=f"openai/{model}",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        ).choices[0].message.content.strip()

        return response

    def chat_with_multiple_transcripts(
        self,
        question: str,
        api_key: str,
        base_url: str,
        model: str,
        transcript_ids: List[int],
        chat_max_windows: int = 1_000_000,
    ) -> str:
        """
        基于多个转录内容进行智能问答。

        对每个transcript_id执行知识检索，合并结果后进行问答。

        参数：
        - question: 用户问题
        - api_key: LLM API密钥
        - base_url: LLM API基础URL
        - model: LLM模型名称
        - chat_max_windows: 最大token限制
        - transcript_ids: 多个转录ID列表

        返回：
        - LLM生成的回答
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
            raise ValueError("No relevant content found in the selected transcripts")

        # 按index排序确保内容连贯
        all_segments.sort(key=lambda s: s.get("index", 0))

        tokens = self._count_tokens_for_segments(all_segments)
        if tokens > chat_max_windows:
            raise ValueError(
                f"input tokens {tokens} exceed chat_max_windows {chat_max_windows}"
            )

        prompt = self._build_multi_video_prompt(all_segments, question, video_info)

        # 设置 LiteLLM 环境变量
        os.environ["OPENAI_API_KEY"] = api_key
        if base_url:
            os.environ["OPENAI_API_BASE"] = base_url

        # 使用 LiteLLM 调用
        response = litellm.completion(
            model=f"openai/{model}",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        ).choices[0].message.content.strip()

        return response


# 全局实例
chat_service = ChatService()