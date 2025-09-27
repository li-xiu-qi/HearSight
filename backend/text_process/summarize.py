# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List
import json

import tiktoken

from backend.chat_utils.chat_client import chat_text
from backend.utils.typing_defs import Segment, SummaryItem



def _count_tokens_for_segments(segments: List[Segment], encoding_name: str = "cl100k_base") -> int:
    """
    最小实现：仅按文本字段统计 token 数。
    说明：不同模型的编码可能不同，这里采用通用的 cl100k_base 以近似估计。
    """
    enc = tiktoken.get_encoding(encoding_name)
    # 仅统计句子文本，避免引入其他结构性字符的误差
    text = "\n".join(s.get("sentence", "") for s in segments)
    return len(enc.encode(text))


def _build_prompt(segments: List[Segment]) -> str:

    header = """
你是一个专业的内容总结助手。请：
1) 提炼对话/内容的主题（topic），并输出一段简明中文总结（summary），准确涵盖主要信息点，避免流水账与冗余重复。
2) 严格只输出一个 JSON 对象，不要包含任何额外说明、前后文本、Markdown、代码块或非 JSON 内容。JSON 格式如下：

{"topic": "<主题短句>", "summary": "<中文总结，允许换行，但不要包含额外的元信息或标签>"}

3) 输出时不要在字符串中再包含“Topic:”或“Summary:”等标签，也不要使用粗体/标题语法。
下面是带时间戳的句子片段：
""".strip()

    body_lines: list[str] = []
    for s in segments:
        st = s.get("start_time", 0.0)
        ed = s.get("end_time", st)
        sent = s.get("sentence", "").strip()
        body_lines.append(f"[{st:.2f}, {ed:.2f}] {sent}")

    footer = """

请先给出主题 topic，再给出中文总结 summary。
""".strip("\n")

    return "\n".join([header, *body_lines, "", footer])


def summarize_segments(
    segments: List[Segment],
    api_key: str,
    base_url: str,
    model: str,
    chat_max_windows: int = 1_000_000,
) -> List[SummaryItem]:
    """一次性生成总结。

    参数：
    - segments：句级片段（无 spk_id）
    - api_key/base_url/model：复用 chat_client 统一配置
    - chat_max_windows：用于限制输入的近似 token 上限（项目内称为 CHAT_MAX_WINDOWS）

    返回：list[SummaryItem]
    - 仅生成一条汇总，时间范围取整体最小/最大时间戳
    """
    if not segments:
        return []

    tokens = _count_tokens_for_segments(segments)
    if tokens > chat_max_windows:
        # 超限直接抛出，由上层决定是否改用分段 Summarization
        raise ValueError(f"input tokens {tokens} exceed chat_max_windows {chat_max_windows}")

    prompt = _build_prompt(segments)

    topic_and_summary = chat_text(
        prompt=prompt,
        api_key=api_key,
        base_url=base_url,
        model=model,
    ).strip()

    # 可能的模型返回形式多样：优先尝试直接解析为 JSON；若失败，再尝试从代码块中提取 JSON（例如 ```json\n{...}```）；最后回退为整体文本
    parsed = False
    try:
        obj = json.loads(topic_and_summary)
        if isinstance(obj, dict):
            topic = str(obj.get('topic') or '').strip()
            summary = str(obj.get('summary') or '').strip()
            parsed = True
    except Exception:
        parsed = False

    if not parsed:
        try:
            # 提取第一个 code fence 内的内容（若有），优先查找包含 JSON 的块
            if '```' in topic_and_summary:
                parts = topic_and_summary.split('```')
                # code fence 在奇数索引处
                for i in range(1, len(parts), 2):
                    block = parts[i].strip()
                    # 支持开头带 json 标记的情况
                    if block.lower().startswith('json'):
                        # 去掉首行的 json 标记
                        block = block.split('\n', 1)[1] if '\n' in block else ''
                    block = block.strip()
                    if not block:
                        continue
                    try:
                        obj = json.loads(block)
                        if isinstance(obj, dict):
                            topic = str(obj.get('topic') or '').strip()
                            summary = str(obj.get('summary') or '').strip()
                            parsed = True
                            break
                    except Exception:
                        continue
        except Exception:
            parsed = False

    start_time = min(s.get("start_time", 0.0) for s in segments)
    end_time = max(s.get("end_time", start_time) for s in segments)

    # 输出一条结果，topic 与 summary 由模型生成文本中解析的简单策略：
    # 约定：模型按“topic: ...\nsummary: ...”返回（提示词已引导先 topic 再 summary），
    # 若未严格遵循，则整体放入 summary，topic 为空。
    topic = ""
    summary = topic_and_summary

    # 优先尝试解析为 JSON（因为提示词要求严格返回 JSON），解析失败则回退为把完整文本作为 summary
    try:
        obj = json.loads(topic_and_summary)
        if isinstance(obj, dict):
            topic = str(obj.get('topic') or '').strip()
            summary = str(obj.get('summary') or '').strip()
    except Exception:
        # 解析失败则保持 topic = "" 且 summary 为原始文本
        topic = ""
        summary = topic_and_summary

    return [
        SummaryItem(
            topic=topic,
            summary=summary,
            start_time=float(start_time),
            end_time=float(end_time),
        )
    ]
