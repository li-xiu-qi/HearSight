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
        search_results = knowledge_base.search_similar(question, n_results=5, transcript_ids=[transcript_id])
        relevant_segments = []
        db_url = None  # connect_db 会使用环境变量
        
        for result in search_results:
            doc_id = result["doc_id"]
            doc_details = knowledge_base.get_doc_details(doc_id, db_url)
            if doc_details and "sentences" in doc_details:
                # 为每个segment添加transcript_id信息
                for segment in doc_details["sentences"]:
                    segment["transcript_id"] = transcript_id
                relevant_segments.extend(doc_details["sentences"])
        
        # 按句子在原视频中的顺序排序，确保内容连贯
        relevant_segments.sort(key=lambda s: s.get("index", 0))
        
        # 获取文件名
        filename = None
        if relevant_segments:
            transcript = get_transcript_by_id(db_url, transcript_id)
            if transcript:
                video_path = transcript.get("video_path")
                audio_path = transcript.get("audio_path")
                if video_path:
                    filename = os.path.basename(video_path)
                elif audio_path:
                    filename = os.path.basename(audio_path)
        
        return relevant_segments, filename

    def _count_tokens_for_segments(self, segments: List[Segment]) -> int:
        """
        计算句子片段的总 token 数。

        参数：
        - segments: 句子片段列表

        返回：
        - 总 token 数
        """
        from backend.utils.token_utils.calculate_tokens import OpenAITokenCalculator
        calculator = OpenAITokenCalculator()
        # 仅统计句子文本，避免引入其他结构性字符的误差
        text = "\n".join(s.get("sentence", "") for s in segments)
        return calculator.count_tokens(text)