"""知识库检索工具"""

import os
import sys
from typing import List, Dict, Any

# 确保backend在路径中
backend_path = os.path.dirname(os.path.dirname(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from backend.services.knowledge_base_service import knowledge_base
from backend.db.transcript_crud import get_transcript_by_id
from backend.schemas import Segment
from backend.ReAct.summary_compressor import summary_compressor


class KnowledgeRetrievalTool:
    """知识库检索工具类"""

    def __init__(self):
        pass

    async def retrieve_knowledge(self, question: str, transcript_ids) -> str:
        """
        从知识库检索相关内容并压缩

        参数:
            question: 用户问题
            transcript_ids: 转录ID或ID列表

        返回:
            压缩后的关键信息字符串
        """
        # 兼容单个ID和列表
        if isinstance(transcript_ids, int):
            transcript_ids = [transcript_ids]
        elif not isinstance(transcript_ids, list):
            return f"无效的transcript_ids参数: {transcript_ids}"

        try:
            all_segments = []
            video_info = []

            # 对每个transcript_id执行检索
            for transcript_id in transcript_ids:
                # 使用异步任务执行检索
                from backend.queues.tasks.process_job_task import knowledge_retrieval_task
                task = knowledge_retrieval_task.delay(question, transcript_id)
                segments, filename = task.get(timeout=30)  # 等待30秒

                if segments:
                    all_segments.extend(segments)
                    if filename:
                        video_info.append({"filename": filename, "transcript_id": transcript_id})

            # 如果没有检索到内容，返回错误
            if not all_segments:
                return "No relevant content found in the selected transcripts"

            # 获取文件名（如果只有一个transcript_id）
            filename = None
            if len(transcript_ids) == 1:
                transcript = get_transcript_by_id(None, transcript_ids[0])
                if transcript:
                    video_path = transcript.get("video_path")
                    audio_path = transcript.get("audio_path")
                    if video_path:
                        filename = os.path.basename(video_path)
                    elif audio_path:
                        filename = os.path.basename(audio_path)

            # 构建检索结果
            retrieval_results = {
                "segments": all_segments,
                "filename": filename or "multiple_files",
                "transcript_id": transcript_ids[0] if len(transcript_ids) == 1 else None,
                "transcript_ids": transcript_ids,
                "question": question,
                "video_info": video_info
            }

            # 压缩检索结果
            compressed_info = await summary_compressor.compress_single_file_results(
                question, retrieval_results
            )

            return compressed_info

        except Exception as e:
            return f"检索失败: {str(e)}"


# 全局实例
retrieval_tool = KnowledgeRetrievalTool()