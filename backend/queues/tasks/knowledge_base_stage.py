# -*- coding: utf-8 -*-
"""知识库处理阶段"""

import logging
from typing import List, Dict, Any, Tuple

from backend.services.knowledge_base_service import knowledge_base
from backend.schemas import Segment

logger = logging.getLogger(__name__)


def handle_knowledge_base_stage(
    job_id: int,
    transcript_id: int,
    segments: List[Dict[str, Any]]
) -> None:
    """处理知识库添加阶段"""
    try:
        # 知识库只存 minimal metadata：transcript_id 与 chunk_index（自动添加）
        metadata = {"transcript_id": transcript_id}

        knowledge_base.add_transcript(
            segments=segments,
            metadata=metadata
        )
        logger.info(f"转写句子段已添加到知识库: job_id={job_id}")
    except Exception as e:
        logger.error(f"添加转写句子段到知识库失败: {str(e)}")
        raise


def handle_knowledge_retrieval_stage(
    question: str,
    transcript_id: int
) -> Tuple[List[Segment], str]:
    """处理知识库检索阶段"""
    try:
        from backend.services.chat_knowledge_service import ChatKnowledgeService
        service = ChatKnowledgeService()
        relevant_segments, filename = service._perform_knowledge_retrieval(question, transcript_id)
        logger.info(f"知识库检索完成: transcript_id={transcript_id}, 检索到 {len(relevant_segments)} 个片段")
        return relevant_segments, filename
    except Exception as e:
        logger.error(f"知识库检索失败: {str(e)}")
        raise