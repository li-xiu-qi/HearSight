# -*- coding: utf-8 -*-
"""
提示词生成模块：为两步翻译法构建高质量的提示词。
"""
from typing import Dict, List, Optional

from backend.schemas import Segment


def build_literal_translate_prompt(
    segments: List[Segment],
    source_lang: str,
    target_lang: str,
    all_segments: Optional[List[Segment]] = None,
) -> str:
    """
    构建直译提示词：强调准确传达信息，不遗漏。
    针对双语翻译优化。
    """
    header = f"""你是一位专业翻译，擅长中英文互译。我希望你能帮我将以下{source_lang}段落直译成{target_lang}。

规则：
- 准确传达原文事实和背景，不要遗漏任何信息
- 保留特定的英文术语或名字，并在其前后加上空格，例如：" AI "、" UN "
- 根据内容直译，保持原文结构和逻辑
- 这是直译步骤，重点是信息完整性

英文原文：
"""

    # 添加原文句子
    content_lines = []
    for seg in segments:
        sentence = (seg.get("sentence") or "").strip()
        if not sentence:
            continue
        index = seg.get("index", 0)
        content_lines.append(f"{index}: {sentence}")

    content = "\n".join(content_lines)

    footer = f"""

直译结果：
请只输出JSON格式的翻译结果：
```json
[{{"index": 0, "translation": "直译内容"}}]
```"""

    return header + content + footer


def build_meaning_translate_prompt(
    segments: List[Segment],
    literal_translations: Dict[int, str],
    source_lang: str,
    target_lang: str,
    all_segments: Optional[List[Segment]] = None,
) -> str:
    """
    构建意译提示词：基于直译结果优化表达，使其更自然。
    针对双语翻译优化。
    """
    header = f"""你是一位专业中英文翻译，擅长对翻译结果进行二次修改和润色。我希望你能帮我将以下{source_lang}的{target_lang}直译结果重新意译和润色。

规则：
- 基于直译结果重新意译，意译时务必对照原始{source_lang}，不要添加也不要遗漏内容
- 让翻译结果通俗易懂，符合{target_lang}表达习惯
- 保留特定的英文术语、数字或名字，并在其前后加上空格，例如：" AI "、" 10 秒"
- 注意专业术语的准确性
- 这是意译步骤，重点是自然流畅的表达

英文原文：
"""

    # 添加原文句子
    original_lines = []
    for seg in segments:
        sentence = (seg.get("sentence") or "").strip()
        if not sentence:
            continue
        index = seg.get("index", 0)
        original_lines.append(f"{index}: {sentence}")

    content = "\n".join(original_lines)

    literal_content = "\n直译结果：\n"
    for seg in segments:
        index = seg.get("index", 0)
        literal = literal_translations.get(index, "")
        literal_content += f"{index}: {literal}\n"

    footer = f"""

意译和润色后：
请只输出JSON格式的最终翻译结果：
```json
[{{"index": 0, "translation": "意译内容"}}]
```"""

    return header + content + literal_content + footer
