"""知识库检索工具"""

import os
from typing import List, Dict, Any
from backend.services.knowledge_base_service import knowledge_base
from backend.db.transcript_crud import get_transcript_by_id
from backend.schemas import Segment
from backend.ReAct.summary_compressor import summary_compressor


class KnowledgeRetrievalTool:
    """知识库检索工具类"""

    def __init__(self):
        pass

    async def retrieve_knowledge(self, question: str, transcript_id: int) -> str:
        """
        从知识库检索相关内容并压缩

        参数:
            question: 用户问题
            transcript_id: 转录ID

        返回:
            压缩后的关键信息字符串
        """
        try:
            # 使用异步任务执行检索
            from backend.queues.tasks.process_job_task import knowledge_retrieval_task
            task = knowledge_retrieval_task.delay(question, transcript_id)
            segments, filename = task.get(timeout=30)  # 等待30秒

            # 获取文件名
            if not filename:
                transcript = get_transcript_by_id(None, transcript_id)
                if transcript:
                    video_path = transcript.get("video_path")
                    audio_path = transcript.get("audio_path")
                    if video_path:
                        filename = os.path.basename(video_path)
                    elif audio_path:
                        filename = os.path.basename(audio_path)

            # 构建检索结果
            retrieval_results = {
                "segments": segments,
                "filename": filename or "unknown",
                "transcript_id": transcript_id,
                "question": question
            }

            # 压缩检索结果
            compressed_info = await summary_compressor.compress_retrieval_results(
                question, retrieval_results
            )

            return compressed_info

        except Exception as e:
            return f"检索失败: {str(e)}"


# 全局实例
retrieval_tool = KnowledgeRetrievalTool()