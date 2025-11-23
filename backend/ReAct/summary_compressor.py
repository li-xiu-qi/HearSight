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

    async def compress_multiple_files_results(
        self,
        question: str,
        retrieval_results_list: List[Dict[str, Any]],
        max_length: int = 2000
    ) -> str:
        """
        压缩多个文件的检索结果为关键信息

        参数:
            question: 用户问题
            retrieval_results_list: 多个检索结果字典的列表
            max_length: 压缩后文本的最大长度

        返回:
            压缩后的关键信息，按文件分类组织
        """
        try:
            if not retrieval_results_list:
                return "未找到相关内容"

            # 收集所有文件的原始内容
            all_content_parts = []
            file_summaries = []

            for retrieval_results in retrieval_results_list:
                segments = retrieval_results.get("segments", [])
                filename = retrieval_results.get("filename", "unknown")

                if not segments:
                    continue

                # 使用层次化标签系统组织内容
                file_content = self._build_hierarchical_content(segments, filename)
                all_content_parts.append(file_content)
                file_summaries.append(f"- {filename}: {len(segments)} 个相关片段")

            if not all_content_parts:
                return "未找到相关内容"

            raw_content = "\n\n".join(all_content_parts)

            # 如果总内容不长，直接返回
            if len(raw_content) <= max_length:
                summary = "\n".join(file_summaries)
                return f"检索结果概览:\n{summary}\n\n详细内容:\n{raw_content}"

            # 内容过长，需要压缩
            compression_prompt = f"""
            请基于用户问题，从以下多个视频文件的检索内容中提取最相关和最重要的信息。

            用户问题: {question}

            检索结果概览:
            {chr(10).join(file_summaries)}

            所有文件的检索内容:
            {raw_content}

            要求:
            1. 按文件分类组织内容，每个文件的内容单独总结
            2. 保留时间戳信息，但只保留最相关的片段
            3. 基于问题相关性进行筛选和排序
            4. 总结关键信息，避免重复
            5. 控制总输出长度在{max_length}字符以内
            6. 保持信息的准确性和连贯性

            示例输出格式:
            文件 video1.mp4:
            主要讨论了人工智能技术[120.50-180.30]，强调了在医疗领域的应用价值。

            文件 video2.mp4:
            介绍了大数据分析方法[45.20-89.15]，展示了实际案例。

            请按文件分类总结最相关的内容:
            """

            response = self.llm_router.completion(
                model=settings.llm_model,
                messages=[{"role": "user", "content": compression_prompt}],
                temperature=0.3,
                max_tokens=1500,
            )

            compressed_content = response.choices[0].message.content.strip()

            return f"多文件压缩总结:\n{compressed_content}"

        except Exception as e:
            # 压缩失败，返回简化的多文件概览
            file_summaries = []
            for retrieval_results in retrieval_results_list:
                filename = retrieval_results.get("filename", "unknown")
                segments = retrieval_results.get("segments", [])
                file_summaries.append(f"- {filename}: {len(segments)} 个片段")

            return f"压缩失败，返回文件概览:\n" + "\n".join(file_summaries)

    def _build_hierarchical_content(self, segments: List[Dict[str, Any]], filename: str) -> str:
        """
        使用层次化标签系统构建文件内容

        参数:
            segments: 句子片段列表
            filename: 文件名

        返回:
            层次化组织的内容字符串
        """
        if not segments:
            return f"[文件开始: {filename}]\n[文件结束: {filename}]"

        content_lines = [f"[文件开始: {filename}]"]

        # 将segments按连续性分组为块
        if segments:
            current_chunk = [segments[0]]
            chunk_start_index = segments[0].get("index", 0)
            chunk_num = 1

            for i in range(1, len(segments)):
                # 检查索引是否连续
                if segments[i].get("index", 0) == segments[i-1].get("index", 0) + 1:
                    current_chunk.append(segments[i])
                else:
                    # 输出当前块
                    chunk_end_index = current_chunk[-1].get("index", 0)
                    content_lines.append(f"  [块开始: {chunk_num} - 索引: {chunk_start_index}-{chunk_end_index}]")
                    for segment in current_chunk:
                        start_time = segment.get("start", 0)
                        end_time = segment.get("end", 0)
                        text = segment.get("text", "").strip()
                        if text:
                            time_str = f"[{start_time:.2f}-{end_time:.2f}]"
                            content_lines.append(f"  {time_str} {text}")
                    content_lines.append(f"  [块结束: {chunk_num}]")
                    content_lines.append("")  # 块间空行

                    # 开始新块
                    current_chunk = [segments[i]]
                    chunk_start_index = segments[i].get("index", 0)
                    chunk_num += 1

            # 输出最后一个块
            if current_chunk:
                chunk_end_index = current_chunk[-1].get("index", 0)
                content_lines.append(f"  [块开始: {chunk_num} - 索引: {chunk_start_index}-{chunk_end_index}]")
                for segment in current_chunk:
                    start_time = segment.get("start", 0)
                    end_time = segment.get("end", 0)
                    text = segment.get("text", "").strip()
                    if text:
                        time_str = f"[{start_time:.2f}-{end_time:.2f}]"
                        content_lines.append(f"  {time_str} {text}")
                content_lines.append(f"  [块结束: {chunk_num}]")

        content_lines.append(f"[文件结束: {filename}]")
        content_lines.append("\n请注意：以上内容来自同一视频的不同块，不保证时间连续性。")

        return "\n".join(content_lines)

    # 向后兼容的别名
    async def compress_retrieval_results(
        self,
        question: str,
        retrieval_results: Dict[str, Any],
        max_length: int = 2000
    ) -> str:
        """
        压缩检索结果为关键信息（向后兼容方法）

        参数:
            question: 用户问题
            retrieval_results: 检索结果字典
            max_length: 压缩后文本的最大长度

        返回:
            压缩后的关键信息
        """
        # 直接调用多文件压缩方法，传入单文件结果列表
        return await self.compress_multiple_files_results(question, [retrieval_results], max_length)