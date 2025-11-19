"""分段规范化工具模块

统一处理 ASR 结果的分段合并和规范化逻辑，避免重复代码。
"""

from typing import Dict, List


def normalize_segments(
    segments: List[Dict],
    merge_sentences: bool = True,
    merge_short_sentences: bool = True,
) -> List[Dict]:
    """规范化 ASR 分段结果

    基于标点符号和句子长度进行句子合并。

    Args:
        segments: 原始分段列表，必须包含 spk_id 和 sentence 字段
        merge_sentences: 是否通过标点符号合并句子
        merge_short_sentences: 是否合并少于 4 个字的句子到下一句

    Returns:
        规范化后的分段列表
    """
    if not segments:
        return []

    # 输入验证
    for segment in segments:
        if "sentence" not in segment or "spk_id" not in segment:
            raise ValueError("每个分段必须包含 'sentence' 和 'spk_id' 字段")

    merge_punctuations = ["，", "；", "：", "、", ",", ";", ":"]

    def ends_with_punctuation(text: str) -> bool:
        return any(text.endswith(punc) for punc in merge_punctuations)

    def can_merge_with_next(current: Dict, next_item: Dict) -> bool:
        return (
            current.get("spk_id") == next_item.get("spk_id")
            and next_item.get("sentence", "").strip()
        )

    merged_results: List[Dict] = []
    i = 0
    while i < len(segments):
        current = segments[i].copy()
        merged = False

        # 优先检查句子合并（基于标点）
        if (
            merge_sentences
            and ends_with_punctuation(current.get("sentence", ""))
            and i + 1 < len(segments)
        ):
            next_item = segments[i + 1]
            if can_merge_with_next(current, next_item):
                current["sentence"] += next_item["sentence"]  # 无空格，直接连接
                current["end_time"] = next_item.get("end_time", current.get("end_time"))
                merged_results.append(current)
                i += 2
                merged = True

        # 检查短句子合并
        if (
            not merged
            and merge_short_sentences
            and i + 1 < len(segments)
        ):
            sent_length = len(current.get("sentence", "").strip())
            if sent_length < 4:
                next_item = segments[i + 1]
                if can_merge_with_next(current, next_item):
                    current["sentence"] += " " + next_item["sentence"]  # 有空格
                    current["end_time"] = next_item.get(
                        "end_time", current.get("end_time")
                    )
                    merged_results.append(current)
                    i += 2
                    merged = True

        if not merged:
            merged_results.append(current)
            i += 1

    # 添加索引
    for idx, item in enumerate(merged_results, start=1):
        item["index"] = idx

    return merged_results


def extract_text(segments: List[Dict]) -> str:
    """从分段列表提取完整文本

    自动处理多余空格，确保文本连贯。
    """
    if not segments:
        return ""

    sentences = []
    for segment in segments:
        sentence = segment.get("sentence", "").strip()
        if sentence:
            sentences.append(sentence)

    # 用单个空格连接，并清理多余空格
    text = " ".join(sentences)
    # 清理多余空格
    import re
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
