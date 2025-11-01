# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List, Dict
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


def _split_segments_by_output_tokens(
    segments: List[Segment],
    max_tokens: int = 4096,
    encoding_name: str = "cl100k_base"
) -> List[List[Segment]]:
    """
    根据预估的总结输出token数，将分句分批。
    
    参数:
    - segments: 要分批的分句列表
    - max_tokens: 每批最大输出token数（默认4096）
    - encoding_name: 编码方式
    
    返回: 分批后的分句列表
    """
    if not segments:
        return []
    
    enc = tiktoken.get_encoding(encoding_name)
    batches = []
    current_batch = []
    current_output_tokens = 0
    
    for seg in segments:
        sentence = seg.get("sentence", "")
        # 估算总结输出的token数（原文的0.8倍作为总结大小）
        estimated_tokens = int(len(enc.encode(sentence)) * 0.8) + 50
        
        if current_output_tokens + estimated_tokens > max_tokens and current_batch:
            # 当前批次满了，开始新批次
            batches.append(current_batch)
            current_batch = [seg]
            current_output_tokens = estimated_tokens
        else:
            current_batch.append(seg)
            current_output_tokens += estimated_tokens
    
    if current_batch:
        batches.append(current_batch)
    
    return batches


def _build_prompt(segments: List[Segment]) -> str:

    header = """
你是一个专业的内容总结助手。请：
1) 仔细分析下面的对话/内容，从中提炼出多个清晰的主题（topic）。
2) 为每个主题生成一段简明中文总结（summary），准确涵盖该主题的主要信息点，避免流水账与冗余重复。
3) 为每个主题指定对应的时间范围，使用该主题相关句子的起始和结束时间戳。
4) 严格按以下格式输出，使用Python代码块语法包围输出结果：

```python
[
    {"topic": "<主题短句>", "summary": "<中文总结，允许换行，但不要包含额外的元信息或标签>", "start_time": <起始时间戳>, "end_time": <结束时间戳>},
    {"topic": "<另一个主题短句>", "summary": "<另一个中文总结>", "start_time": <起始时间戳>, "end_time": <结束时间戳>}
]
```

5) 请根据内容的复杂度和信息量，合理确定主题数量，通常在2-5个之间。
6) 不要包含任何额外说明、前后文本或其他格式。

下面是带时间戳的句子片段：
""".strip()

    body_lines: list[str] = []
    for s in segments:
        st = s.get("start_time", 0.0)
        ed = s.get("end_time", st)
        sent = s.get("sentence", "").strip()
        # 优化时间戳格式，使用更清晰的分隔符
        body_lines.append(f"[{st:.2f}-{ed:.2f}] {sent}")

    footer = """

请仔细分析内容，按指定格式输出，确保每个主题的时间范围准确反映其对应的句子时间。
""".strip("\n")

    return "\n".join([header, *body_lines, "", footer])


def _extract_python_summaries(response_text: str) -> List[Dict[str, str]]:
    """
    从模型响应中提取Python代码块格式的总结数据。
    
    参数:
    - response_text: 模型返回的原始文本
    
    返回:
    - 包含主题和总结的字典列表
    """
    summaries = []
    
    # 只处理```python代码块格式
    try:
        if '```python' in response_text:
            parts = response_text.split('```python')
            if len(parts) > 1:
                # 获取第一个Python代码块
                block = parts[1].split('```')[0].strip()
                if block:
                    # 使用eval安全地执行Python代码（仅限列表和字典）
                    parsed_summaries = eval(block, {"__builtins__": {}}, {})
                    if isinstance(parsed_summaries, list):
                        for item in parsed_summaries:
                            if isinstance(item, dict) and 'topic' in item and 'summary' in item:
                                # 提取主题、总结和时间戳信息
                                summary_item = {
                                    'topic': str(item['topic']).strip(),
                                    'summary': str(item['summary']).strip()
                                }
                                # 尝试提取时间戳信息
                                if 'start_time' in item:
                                    summary_item['start_time'] = str(float(item['start_time']))
                                if 'end_time' in item:
                                    summary_item['end_time'] = str(float(item['end_time']))
                                summaries.append(summary_item)
    except Exception:
        pass  # 解析失败

    return summaries


def summarize_segments(
    segments: List[Segment],
    api_key: str,
    base_url: str,
    model: str,
    chat_max_windows: int = 1_000_000,
    max_tokens: int = 4096,
) -> List[SummaryItem]:
    """生成多个主题的总结，支持分批处理长内容。

    参数：
    - segments：句级片段
    - api_key/base_url/model：复用 chat_client 统一配置
    - chat_max_windows：用于限制输入的近似 token 上限（项目内称为 CHAT_MAX_WINDOWS）
    - max_tokens：每批总结的最大输出token数（默认4096）

    返回：list[SummaryItem]
    - 生成多个主题的总结，每个总结有独立的时间范围
    """
    if not segments:
        return []

    tokens = _count_tokens_for_segments(segments)
    if tokens > chat_max_windows:
        # 超限时进行分批处理
        batches = _split_segments_by_output_tokens(segments, max_tokens)
        all_summaries: List[SummaryItem] = []
        
        for batch in batches:
            batch_summaries = summarize_segments(
                batch,
                api_key=api_key,
                base_url=base_url,
                model=model,
                chat_max_windows=chat_max_windows,
                max_tokens=max_tokens,
            )
            all_summaries.extend(batch_summaries)
        
        return all_summaries

    prompt = _build_prompt(segments)

    topic_and_summary = chat_text(
        prompt=prompt,
        api_key=api_key,
        base_url=base_url,
        model=model,
        max_tokens=max_tokens,
    ).strip()

    # 初始化返回值
    summaries = []
    overall_start_time = min(s.get("start_time", 0.0) for s in segments)
    overall_end_time = max(s.get("end_time", overall_start_time) for s in segments)

    # 使用新函数提取Python代码块总结
    extracted_summaries = _extract_python_summaries(topic_and_summary)
    
    # 为每个提取到的主题创建SummaryItem
    for item in extracted_summaries:
        # 如果模型提供了时间戳信息，则使用模型提供的时间戳，否则使用整体时间范围
        start_time = float(item.get('start_time', overall_start_time))
        end_time = float(item.get('end_time', overall_end_time))
        
        summaries.append(SummaryItem(
            topic=item['topic'],
            summary=item['summary'],
            start_time=start_time,
            end_time=end_time,
        ))

    # 如果解析失败或没有解析到任何内容，回退为将整个响应作为单个总结
    if not summaries:
        summaries.append(SummaryItem(
            topic="",
            summary=topic_and_summary,
            start_time=float(overall_start_time),
            end_time=float(overall_end_time),
        ))

    return summaries