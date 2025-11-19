# -*- coding: utf-8 -*-
"""
提示词生成模块：为翻译任务构建高质量的提示词，包含上下文信息。
"""
from typing import List, Optional

from backend.schemas import Segment


def build_translate_prompt(
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
    header = f"""# 翻译任务：{source_lang} → {target_lang}

## 输入格式
- `index: 原句`
- index 从 0 开始，仅用于标识
- 原句保持原始大小写与符号

## 输出格式
```
translation_content:
```json
[{{"index": 0, "translation": "示例翻译"}}]
```
```

## 必须遵守
- 保持 index 对应，一句一译
- 忠实传达原意，不得增删解释
- 只输出上述 JSON 代码块
""".strip()

    lines = [header, "待翻译句子："]

    for seg in segments:
        sentence = (seg.get("sentence") or "").strip()
        if not sentence:
            continue
        index = seg.get("index", 0)
        lines.append(f"{index}: {sentence}")

    return "\n".join(lines)
