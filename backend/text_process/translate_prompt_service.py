# -*- coding: utf-8 -*-
"""
翻译提示词构建模块：构建翻译提示词。
"""

from __future__ import annotations

from typing import List, Optional

from backend.schemas import Segment


def _build_translate_prompt(
    segments: List[Segment],
    source_lang: str,
    target_lang: str,
    all_segments: Optional[List[Segment]] = None,
) -> str:
    """
    构建翻译提示词，支持任意语言对，包含上下文信息。

    参数:
    - segments: 本批次要翻译的分句列表（约 10 句）
    - source_lang: 源语言名称（如 "English", "Chinese", "Japanese"）
    - target_lang: 目标语言名称
    - all_segments: 完整的分句列表（用于提供上下文，仅供参考）
    """
    header = f"""你是一个专业的{source_lang}至{target_lang}翻译专家。

翻译要求：
1. 准确传达原文含义，不要改变、扩展或删减原文内容
2. 保持原文的风格、语气和情感色彩
3. 保留专业术语和专有名词（如人名、地名、技术术语等）
4. 使用目标语言最自然的表达方式，避免生硬翻译
5. 不同语言的翻译长度可能差异很大，这是完全正常的（例如英文"Hello"可能翻译为中文"你好"）

关键要求 - 索引对应规则（必须严格遵守）：
- 【重要】每个翻译结果的 index 必须与【待翻译句子】中的 index 完全相同
- 【重要】每句话都有唯一的 index 标识符，返回的翻译必须一一对应
- 【重要】绝不能漏掉任何一句，绝不能改变顺序，绝不能重复
- 【重要】如果你注意到 index 不是连续的（如 0, 1, 3, 5），这是正常的，保持原样即可

工作流程：
1. 首先阅读【前文上下文】和【后文上下文】以了解语境（但这些内容本身不需要翻译）
2. 然后专注于翻译【待翻译句子】中的所有句子（只翻译这一部分）
3. 逐一确认每个句子都有唯一的翻译结果，index 必须完全对应

返回要求：
- 返回结果必须严格包含 START_TRANSLATIONS 和 END_TRANSLATIONS 边界标记
- 边界标记之间只能包含纯JSON数组格式
- JSON 数组必须包含所有待翻译句子的翻译结果（一个都不能少）
- 每个待翻译句子都必须有一个翻译条目，格式必须是（注意是单个大括号）: {"index": N, "translation": "翻译内容"}
- 严禁混入前文上下文或后文上下文的内容
- 禁止使用Markdown、代码块（```）、加粗、列表、编号等特殊格式

格式示例1（注意：假设待翻译句子的 index 是 0, 1, 2）：

START_TRANSLATIONS
[
  {"index": 0, "translation": "翻译后的句子0"},
  {"index": 1, "translation": "翻译后的句子1"},
  {"index": 2, "translation": "翻译后的句子2"}
]
END_TRANSLATIONS

格式示例2（假设输入 index 是 5, 7, 9）：

START_TRANSLATIONS
[
  {"index": 5, "translation": "翻译后的句子"},
  {"index": 7, "translation": "翻译后的句子"},
  {"index": 9, "translation": "翻译后的句子"}
]
END_TRANSLATIONS
""".strip()

    # 构建上下文部分
    context_lines = [header, ""]

    if all_segments is None:
        all_segments = segments

    # 获取第一个和最后一个要翻译句子的索引
    first_idx = segments[0].get("index", 0) if segments else 0
    last_idx = segments[-1].get("index", 0) if segments else 0

    # 添加前文上下文（前两句，如果存在）
    if first_idx > 0:
        context_lines.append("【前文上下文（仅供参考）】")
        prev_segments = []
        for seg in all_segments:
            seg_idx = seg.get("index", 0)
            if seg_idx < first_idx:
                prev_segments.append((seg_idx, seg))

        if prev_segments:
            for seg_idx, seg in prev_segments[-2:]:
                context_lines.append(f"{seg_idx}: {seg.get('sentence', '').strip()}")
            context_lines.append("")

    # 添加待翻译句子（这是唯一需要翻译的部分）
    context_lines.append("【待翻译句子】（必须逐一翻译，index必须一一对应）")
    for seg in segments:
        index = seg.get("index", 0)
        sentence = seg.get("sentence", "").strip()
        if sentence:
            context_lines.append(f"{index}: {sentence}")
    context_lines.append("")
    context_lines.append(
        f"（共 {len(segments)} 个句子需要翻译，检查：是否一个都没漏，是否顺序没乱，是否 index 完全对应）"
    )

    # 添加后文上下文（后两句，如果存在）
    max_idx = max((seg.get("index", 0) for seg in all_segments), default=0)
    if last_idx < max_idx:
        context_lines.append("【后文上下文（仅供参考）】")
        next_segments = []
        for seg in all_segments:
            seg_idx = seg.get("index", 0)
            if seg_idx > last_idx:
                next_segments.append((seg_idx, seg))

        if next_segments:
            for seg_idx, seg in next_segments[:2]:
                context_lines.append(f"{seg_idx}: {seg.get('sentence', '').strip()}")
            context_lines.append("")

    return "\n".join(context_lines)