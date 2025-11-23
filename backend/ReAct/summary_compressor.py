"""检索结果信息压缩器"""

import json
from typing import List, Dict, Any
from backend.startup import get_llm_router
from backend.config import settings


class RetrievalSummaryCompressor:
    """检索结果信息压缩器

    负责将冗长的检索结果压缩为关键信息，避免记忆爆炸。
    """

    def __init__(self):
        self.llm_router = get_llm_router()

    async def compress_retrieval_results(
        self,
        question: str,
        retrieval_results: Dict[str, Any],
        max_length: int = 2000
    ) -> str:
        """
        压缩检索结果为关键信息

        参数:
            question: 用户问题
            retrieval_results: 检索结果字典
            max_length: 压缩后文本的最大长度

        返回:
            压缩后的关键信息
        """
        try:
            # 提取segments内容
            segments = retrieval_results.get("segments", [])
            filename = retrieval_results.get("filename", "unknown")

            if not segments:
                return "未找到相关内容"

            # 构建原始内容文本
            content_parts = []
            for segment in segments:
                text = segment.get("text", "").strip()
                start_time = segment.get("start", 0)
                end_time = segment.get("end", 0)
                if text:
                    # 格式化为时间戳+文本
                    time_str = f"[{start_time:.0f}-{end_time:.0f}]"
                    content_parts.append(f"{time_str} {text}")

            raw_content = "\n".join(content_parts)

            # 如果内容不长，直接返回
            if len(raw_content) <= max_length:
                return f"来源文件: {filename}\n\n检索内容:\n{raw_content}"

            # 内容过长，需要压缩
            compression_prompt = f"""
            请基于用户问题，从以下视频转录内容中提取最相关和最重要的信息。

            用户问题: {question}

            原始检索内容 (来自文件: {filename}):
            {raw_content}

            要求:
            1. 保留时间戳信息，但只保留最相关的片段
            2. 总结关键信息，避免重复
            3. 控制输出长度在{max_length}字符以内
            4. 保持信息的准确性和连贯性
            5. 如果有多个相关片段，按时间顺序组织

            请用简洁的语言总结最相关的内容:
            """

            response = self.llm_router.completion(
                model=settings.llm_model,
                messages=[{"role": "user", "content": compression_prompt}],
                temperature=0.3,
                max_tokens=1000,
            )

            compressed_content = response.choices[0].message.content.strip()

            return f"来源文件: {filename}\n\n压缩总结:\n{compressed_content}"

        except Exception as e:
            # 压缩失败，返回原始内容的前一部分
            segments = retrieval_results.get("segments", [])
            filename = retrieval_results.get("filename", "unknown")

            content_parts = []
            for segment in segments[:5]:  # 只取前5个片段
                text = segment.get("text", "").strip()
                start_time = segment.get("start", 0)
                end_time = segment.get("end", 0)
                if text:
                    time_str = f"[{start_time:.0f}-{end_time:.0f}]"
                    content_parts.append(f"{time_str} {text}")

            raw_content = "\n".join(content_parts)
            return f"来源文件: {filename}\n\n检索内容 (压缩失败):\n{raw_content}"


# 全局实例
summary_compressor = RetrievalSummaryCompressor()