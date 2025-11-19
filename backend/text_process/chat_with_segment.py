# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List, Dict
import json

import tiktoken

from backend.chat_utils.chat_client import chat_text
from backend.schemas import Segment


def _count_tokens_for_segments(
    segments: List[Segment], encoding_name: str = "cl100k_base"
) -> int:
    """
    最小实现：仅按文本字段统计 token 数。
    说明：不同模型的编码可能不同，这里采用通用的 cl100k_base 以近似估计。
    """
    enc = tiktoken.get_encoding(encoding_name)
    # 仅统计句子文本，避免引入其他结构性字符的误差
    text = "\n".join(s.get("sentence", "") for s in segments)
    return len(enc.encode(text))


def _build_prompt(segments: List[Segment], question: str) -> str:
    """
    构建聊天提示词。

    参数：
    - segments：句级片段
    - question：用户问题

    返回：
    - 构建好的提示词
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

输出示例1（引用字幕内容时）：

人工智能在多个领域都有广泛应用。[92000.00-113620.00]

特别是在医疗领域，人工智能可以帮助医生进行疾病诊断。[121540.00-145440.00]

输出示例2（通用问题时）：

你好！有什么我可以帮你的吗？

用户问题：{question}

视频字幕内容（时间戳格式：[开始时间-结束时间] 字幕内容）：
""".strip()

    body_lines: list[str] = []
    for s in segments:
        st = s.get("start_time", 0.0)
        ed = s.get("end_time", st)
        sent = s.get("sentence", "").strip()
        # 保持原始毫秒单位，不进行转换
        # 优化时间戳格式，使用更清晰的分隔符
        body_lines.append(f"[{st:.2f}-{ed:.2f}] {sent}")

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


def chat_with_segments(
    segments: List[Segment],
    question: str,
    api_key: str,
    base_url: str,
    model: str,
    chat_max_windows: int = 1_000_000,
) -> str:
    """基于分句内容进行问答。

    参数：
    - segments：句级片段
    - question：用户问题
    - api_key/base_url/model：复用 chat_client 统一配置
    - chat_max_windows：用于限制输入的近似 token 上限

    返回：AI回答的文本
    """
    if not segments:
        return "没有可用的字幕内容。"

    tokens = _count_tokens_for_segments(segments)
    if tokens > chat_max_windows:
        raise ValueError(
            f"input tokens {tokens} exceed chat_max_windows {chat_max_windows}"
        )

    prompt = _build_prompt(segments, question)

    response = chat_text(
        prompt=prompt,
        api_key=api_key,
        base_url=base_url,
        model=model,
    ).strip()

    return response
