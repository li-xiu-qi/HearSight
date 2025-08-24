# -*- coding: utf-8 -*-
"""
基于句级段落列表生成一次性总结：
- 输入：list[Segment]（无 spk_id）
- 流程：计算 token（tiktoken），若不超过 max_tokens（默认 100_000）则一次性汇总
- 输出：list[SummaryItem]，形如：
  [
    {
      "topic": str,
      "summary": str,
      "start_time": float,
      "end_time": float,
    }
  ]

依赖：
- tiktoken（requirements.txt 已包含）
- backend.chat_utils.chat_client.chat_text（使用已有的统一聊天调用）

注意：
- 遵循项目偏好：TypedDict 作类型定义；避免过度 try/except；直接调用而非 argparse。
"""
from __future__ import annotations

from typing import List

import tiktoken

from backend.chat_utils.chat_client import chat_text
from backend.utils.typing_defs import Segment, SummaryItem


 
def _count_tokens_for_segments(segments: List[Segment], encoding_name: str = "cl100k_base") -> int:
    """最小实现：仅按文本字段统计 token 数。
    说明：不同模型的编码可能不同，这里采用通用的 cl100k_base 以近似估计。
    """
    enc = tiktoken.get_encoding(encoding_name)
    # 仅统计句子文本，避免引入其他结构性字符的误差
    text = "\n".join(s.get("sentence", "") for s in segments)
    return len(enc.encode(text))


def _build_prompt(segments: List[Segment]) -> str:
    """构造一次性总结提示词。包含：
    - 任务：抽取主题 topic，并给出 concise summary
    - 约束：使用中文、简洁准确，不要重复原文
    - 上下文：提供带时间戳的句子列表
    - 输出风格：不必再包裹 JSON，由上层封装
    """
    header = """
你是一个专业的内容总结助手。请：
1) 提炼对话/内容的主题（topic）。
2) 输出一段简明中文总结（summary），准确涵盖主要信息点，避免流水账与冗余重复。
3) 不要包含无关客套话。
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
    max_tokens: int = 100_000,
) -> List[SummaryItem]:
    """一次性生成总结。

    参数：
    - segments：句级片段（无 spk_id）
    - api_key/base_url/model：复用 chat_client 统一配置
    - max_tokens：最大 token 限制（仅对输入片段计数）

    返回：list[SummaryItem]
    - 仅生成一条汇总，时间范围取整体最小/最大时间戳
    """
    if not segments:
        return []

    tokens = _count_tokens_for_segments(segments)
    if tokens > max_tokens:
        # 超限直接抛出，由上层决定是否改用分段 Summarization
        raise ValueError(f"input tokens {tokens} exceed max_tokens {max_tokens}")

    prompt = _build_prompt(segments)

    topic_and_summary = chat_text(
        prompt=prompt,
        api_key=api_key,
        base_url=base_url,
        model=model,
    ).strip()

    start_time = min(s.get("start_time", 0.0) for s in segments)
    end_time = max(s.get("end_time", start_time) for s in segments)

    # 输出一条结果，topic 与 summary 由模型生成文本中解析的简单策略：
    # 约定：模型按“topic: ...\nsummary: ...”返回（提示词已引导先 topic 再 summary），
    # 若未严格遵循，则整体放入 summary，topic 为空。
    topic = ""
    summary = topic_and_summary
    lower = topic_and_summary.lower()
    # 简单解析：寻找以 topic: / summary: 开头的行
    lines = [l.strip() for l in topic_and_summary.splitlines() if l.strip()]
    if lines:
        # 优先在多行文本里抽取
        tmp_topic = None
        tmp_summary_lines: list[str] = []
        for ln in lines:
            lnl = ln.lower()
            if lnl.startswith("topic:"):
                tmp_topic = ln.split(":", 1)[1].strip()
                continue
            if lnl.startswith("summary:"):
                tmp_summary_lines.append(ln.split(":", 1)[1].strip())
                continue
            # 其他行默认归入 summary
            tmp_summary_lines.append(ln)
        if tmp_topic is not None:
            topic = tmp_topic
            summary = "\n".join(tmp_summary_lines).strip()

    return [
        SummaryItem(
            topic=topic,
            summary=summary,
            start_time=float(start_time),
            end_time=float(end_time),
        )
    ]
