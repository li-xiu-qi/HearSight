# -*- coding: utf-8 -*-
"""聊天提示词构建服务模块"""

import os
from typing import List, Dict, Optional

from backend.schemas import Segment


class ChatPromptService:
    """聊天提示词构建服务类"""

    def _build_prompt(self, segments: List[Segment], question: str, is_from_retrieval: bool = False, filename: str = None) -> str:
        """
        构建聊天提示词。

        根据是否来自检索，使用不同的格式：
        - 检索内容：层次化标签系统
        - 常规内容：标准时间戳格式

        参数：
        - segments: 句子片段列表
        - question: 用户问题
        - is_from_retrieval: 是否来自知识库检索
        - filename: 文件名（检索时需要）

        返回：
        - 完整的提示词字符串
        """
        header = f"""
你是一个专业的视频内容分析助手。请基于下面的视频字幕内容，使用代码格式回答用户的问题。

要求：
1) 仔细分析字幕内容，准确回答用户问题
2) 回答中引用相关内容时，严格遵守时间戳放置规则：
   - 以段落为单位组织回答内容
   - 每个段落只能在末尾添加一个时间戳，格式为：[开始时间-结束时间]
   - 时间戳必须放在段落末尾，前面不能有任何内容（除了段落文本）
   - 时间戳后需要换行，以便区分不同段落
   - 禁止在句子中间或句子末尾添加时间戳（除非整个段落只有一个句子）
3) 时间戳格式要求：
   - 使用毫秒为单位，保留两位小数
   - 使用连字符(-)分隔开始时间和结束时间
4) 时间戳格式示例：
   - 正确：人工智能在多个领域都有广泛应用。[92000.00-113620.00]
   - 错误：人工智能在医疗领域可以帮助医生诊断疾病[121540.00-145440.00]，在教育领域可以个性化辅导学生。
5) 保持回答简洁清晰，使用中文
6) 特别注意：对于与视频内容无关的通用问题（如打招呼、感谢、确认类问题等），请直接简洁回答，不要引用字幕内容，也不需要添加时间戳。

通用问题示例：
- "你好"、"您好"、"hello"
- "谢谢"、"感谢"
- "是的"、"好的"、"明白了"
- "再见"、"拜拜"

用户问题：{question}

视频字幕内容（时间戳格式：[开始时间-结束时间] 字幕内容）：
""".strip()

        if is_from_retrieval and filename:
            # 使用层次化标签系统
            body_lines = self._build_retrieval_prompt_body(segments, filename)
            footer = "\n请注意：以上内容来自同一视频的不同块，不保证时间连续性。"
        else:
            # 原始逻辑
            body_lines = self._build_regular_prompt_body(segments)
            footer = """

请严格按照以下规则回答：
1. 仔细分析字幕内容，准确回答用户问题
2. 时间戳放置是关键，必须遵守：
   - 每个段落只能在末尾添加一个时间戳
   - 时间戳必须放在段落末尾，前面不能有其他内容
   - 时间戳后必须换行
   - 禁止在句子中间插入时间戳
3. 时间戳使用毫秒为单位
4. 对于通用问题请直接简洁回答，不要引用字幕内容，也不需要添加时间戳
""".strip(
                "\n"
            )

        return "\n".join([header, *body_lines, "", footer])

    def _build_retrieval_prompt_body(self, segments: List[Segment], filename: str) -> List[str]:
        """
        构建检索内容的提示词主体。

        使用层次化标签：[文件开始/结束] 和 [块开始/结束]。

        参数：
        - segments: 检索到的句子片段（已排序）
        - filename: 来源文件名

        返回：
        - 提示词主体行列表
        """
        body_lines = [f"[文件开始: {filename}]"]
        
        # 将segments按连续性分组为块
        if segments:
            current_chunk = [segments[0]]
            chunk_start_index = segments[0].get("index", 0)
            chunk_num = 1
            
            for i in range(1, len(segments)):
                if segments[i].get("index", 0) == segments[i-1].get("index", 0) + 1:
                    current_chunk.append(segments[i])
                else:
                    # 输出当前块
                    chunk_end_index = current_chunk[-1].get("index", 0)
                    body_lines.append(f"  [块开始: {chunk_num} - 索引: {chunk_start_index}-{chunk_end_index}]")
                    for s in current_chunk:
                        st = s.get("start_time", 0.0)
                        ed = s.get("end_time", st)
                        sent = s.get("sentence", "").strip()
                        body_lines.append(f"  [{st:.2f}-{ed:.2f}] {sent}")
                    body_lines.append(f"  [块结束: {chunk_num}]")
                    body_lines.append("")  # 块间空行
                    
                    # 开始新块
                    current_chunk = [segments[i]]
                    chunk_start_index = segments[i].get("index", 0)
                    chunk_num += 1
            
            # 输出最后一个块
            if current_chunk:
                chunk_end_index = current_chunk[-1].get("index", 0)
                body_lines.append(f"  [块开始: {chunk_num} - 索引: {chunk_start_index}-{chunk_end_index}]")
                for s in current_chunk:
                    st = s.get("start_time", 0.0)
                    ed = s.get("end_time", st)
                    sent = s.get("sentence", "").strip()
                    body_lines.append(f"  [{st:.2f}-{ed:.2f}] {sent}")
                body_lines.append(f"  [块结束: {chunk_num}]")
        
        body_lines.append(f"[文件结束: {filename}]")
        return body_lines

    def _build_regular_prompt_body(self, segments: List[Segment]) -> List[str]:
        """
        构建常规内容的提示词主体。

        使用标准格式：[开始时间-结束时间] 句子内容

        参数：
        - segments: 句子片段列表

        返回：
        - 提示词主体行列表
        """
        body_lines = []
        for s in segments:
            st = s.get("start_time", 0.0)
            ed = s.get("end_time", st)
            sent = s.get("sentence", "").strip()
            body_lines.append(f"[{st:.2f}-{ed:.2f}] {sent}")
        return body_lines

    def _build_multi_video_prompt(self, segments: List[Segment], question: str, video_info: List[Dict]) -> str:
        """
        构建多视频问答的提示词。

        使用多视频层次化标签：[视频开始/结束] 和 [块开始/结束]。

        参数：
        - segments: 检索到的句子片段（已排序）
        - question: 用户问题
        - video_info: 视频信息列表，包含filename和transcript_id

        返回：
        - 完整的提示词
        """
        header = f"""
你是一个专业的多视频内容分析助手。请基于下面的多个视频字幕内容，使用代码格式回答用户的问题。

要求：
1) 仔细分析所有视频的字幕内容，准确回答用户问题
2) 回答中引用相关内容时，严格遵守时间戳放置规则：
   - 以段落为单位组织回答内容
   - 每个段落只能在末尾添加一个时间戳，格式为：[视频名 开始时间-结束时间]
   - 时间戳必须放在段落末尾，前面不能有任何内容（除了段落文本）
   - 时间戳后需要换行，以便区分不同段落
   - 禁止在句子中间或句子末尾添加时间戳（除非整个段落只有一个句子）
3) 时间戳格式要求：
   - 使用毫秒为单位，保留两位小数
   - 使用连字符(-)分隔开始时间和结束时间
   - 包含视频名称：[视频名 92000.00-113620.00]
4) 时间戳格式示例：
   - 正确：人工智能在多个领域都有广泛应用。[example.mp4 92000.00-113620.00]
   - 错误：人工智能在医疗领域可以帮助医生诊断疾病[example.mp4 121540.00-145440.00]，在教育领域可以个性化辅导学生。
5) 保持回答简洁清晰，使用中文
6) 特别注意：对于与视频内容无关的通用问题（如打招呼、感谢、确认类问题等），请直接简洁回答，不要引用字幕内容，也不需要添加时间戳。

通用问题示例：
- "你好"、"您好"、"hello"
- "谢谢"、"感谢"
- "是的"、"好的"、"明白了"
- "再见"、"拜拜"

输出示例1（引用字幕内容时）：

人工智能在多个领域都有广泛应用。[example.mp4 92000.00-113620.00]

特别是在医疗领域，人工智能可以帮助医生进行疾病诊断。[video1.mp4 121540.00-145440.00]

输出示例2（通用问题时）：

你好！有什么我可以帮你的吗？

用户问题：{question}

多视频字幕内容：
""".strip()

        body_lines = self._build_multi_video_prompt_body(segments, video_info)
        return header + "\n" + "\n".join(body_lines)

    def _build_multi_video_prompt_body(self, segments: List[Segment], video_info: List[Dict]) -> List[str]:
        """
        构建多视频内容的提示词主体。

        使用多视频层次化标签：[视频开始/结束] 和 [块开始/结束]。

        参数：
        - segments: 检索到的句子片段（已排序）
        - video_info: 视频信息列表

        返回：
        - 提示词主体行列表
        """
        body_lines = []

        # 按transcript_id分组segments
        segments_by_video = {}
        for segment in segments:
            transcript_id = segment.get("transcript_id")
            if transcript_id not in segments_by_video:
                segments_by_video[transcript_id] = []
            segments_by_video[transcript_id].append(segment)

        # 为每个视频构建内容
        for video in video_info:
            transcript_id = video["transcript_id"]
            filename = video["filename"]
            video_segments = segments_by_video.get(transcript_id, [])

            if not video_segments:
                continue

            body_lines.append(f"[视频开始: {filename}]")

            # 将segments按连续性分组为块
            if video_segments:
                current_chunk = [video_segments[0]]
                chunk_start_index = video_segments[0].get("index", 0)
                chunk_num = 1

                for i in range(1, len(video_segments)):
                    if video_segments[i].get("index", 0) == video_segments[i-1].get("index", 0) + 1:
                        current_chunk.append(video_segments[i])
                    else:
                        # 输出当前块
                        chunk_end_index = current_chunk[-1].get("index", 0)
                        body_lines.append(f"  [块开始: {chunk_num} - 索引: {chunk_start_index}-{chunk_end_index}]")
                        for s in current_chunk:
                            st = s.get("start_time", 0.0)
                            ed = s.get("end_time", st)
                            sent = s.get("sentence", "").strip()
                            body_lines.append(f"  [{filename} {st:.2f}-{ed:.2f}] {sent}")
                        body_lines.append(f"  [块结束: {chunk_num}]")
                        body_lines.append("")  # 块间空行

                        # 开始新块
                        current_chunk = [video_segments[i]]
                        chunk_start_index = video_segments[i].get("index", 0)
                        chunk_num += 1

                # 输出最后一个块
                if current_chunk:
                    chunk_end_index = current_chunk[-1].get("index", 0)
                    body_lines.append(f"  [块开始: {chunk_num} - 索引: {chunk_start_index}-{chunk_end_index}]")
                    for s in current_chunk:
                        st = s.get("start_time", 0.0)
                        ed = s.get("end_time", st)
                        sent = s.get("sentence", "").strip()
                        body_lines.append(f"  [{filename} {st:.2f}-{ed:.2f}] {sent}")
                    body_lines.append(f"  [块结束: {chunk_num}]")

            body_lines.append(f"[视频结束: {filename}]")
            body_lines.append("")  # 视频间空行

        return body_lines