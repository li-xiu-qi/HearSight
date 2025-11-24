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
        # 直接执行检索，避免在任务中调用任务
        search_results = knowledge_base.search_similar(query=question, n_results=5, transcript_ids=[transcript_id])
        
        all_segments = []
        for result in search_results:
            doc_id = result.get("doc_id")
            if doc_id:
                # 获取文档详情，包括segments
                doc_details = knowledge_base.get_doc_details(doc_id, None)  # db_url暂时设为None，需要传递
                
                if doc_details and doc_details.get("sentences"):
                    all_segments.extend(doc_details["sentences"])
        
        
        # 获取文件名
        transcript = get_transcript_by_id(None, transcript_id)
        filename = "未知文件"
        if transcript:
            video_path = transcript.get("video_path")
            audio_path = transcript.get("audio_path")
            if video_path:
                filename = os.path.basename(video_path)
            elif audio_path:
                filename = os.path.basename(audio_path)
        
        return all_segments, filename

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