# -*- coding: utf-8 -*-
"""聊天知识检索服务模块"""

import os
from typing import List, Dict, Optional, Tuple

from backend.schemas import Segment
from backend.services.knowledge_base_service import knowledge_base
from backend.db.transcript_crud import get_transcript_by_id


class ChatKnowledgeService:
    """聊天知识检索服务类"""

    def _perform_knowledge_retrieval(self, question: str, transcript_id: int) -> tuple[List[Segment], str]:
        """
        执行知识检索。

        从向量数据库中检索相关片段，按index排序。

        参数：
        - question: 用户问题
        - transcript_id: 转录ID

        返回：
        - (相关片段列表, 来源文件名)
        """
        # 使用异步任务执行检索（暂时同步等待结果）
        from backend.queues.tasks.process_job_task import knowledge_retrieval_task
        task = knowledge_retrieval_task.delay(question, transcript_id)
        return task.get(timeout=30)  # 等待30秒

    def _count_tokens_for_segments(self, segments: List[Segment]) -> int:
        """
        计算句子片段的总 token 数。

        参数：
        - segments: 句子片段列表

        返回：
        - 总 token 数
        """
        from backend.utils.token_utils.calculate_tokens import count_segments_tokens
        return count_segments_tokens(segments)