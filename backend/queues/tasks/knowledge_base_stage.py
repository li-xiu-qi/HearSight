# -*- coding: utf-8 -*-
"""知识库处理阶段"""

import logging
from typing import List, Dict, Any

from backend.services.knowledge_base_service import knowledge_base

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
            video_id=str(job_id),
            segments=segments,
            metadata=metadata
        )
        logger.info(f"转写句子段已添加到知识库: job_id={job_id}")
    except Exception as e:
        logger.error(f"添加转写句子段到知识库失败: {str(e)}")
        raise