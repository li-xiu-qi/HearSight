# -*- coding: utf-8 -*-
"""
分批处理模块：将分句按照数量和token限制进行分批。
"""
from typing import List

from backend.schemas import Segment
from backend.utils.token_utils.calculate_tokens import OpenAITokenCalculator


def split_segments_by_output_tokens(
    segments: List[Segment], max_tokens: int = 4096
) -> List[List[Segment]]:
    """
    根据预估的翻译输出token数和句子数量，将分句分批。
    目标：每批约 10 句左右，但不超过 max_tokens 限制。

    参数:
    - segments: 要分批的分句列表
    - max_tokens: 每批最大输出token数（默认4096）

    返回: 分批后的分句列表
    """
    if not segments:
        return []

    # 目标：每批约 10 句
    target_batch_size = 10

    # 先按数量分批，然后检查 token 限制
    batches = []
    for i in range(0, len(segments), target_batch_size):
        batch = segments[i : i + target_batch_size]
        batches.append(batch)

    # 如果某个批次过大（token 超限），则进一步拆分
    calculator = OpenAITokenCalculator()
    final_batches = []

    for batch in batches:
        # 估算这个批次的总 token 数
        total_tokens = 0
        for seg in batch:
            sentence = seg.get("sentence", "")
            estimated_tokens = int(calculator.count_tokens(sentence) * 1.5) + 20
            total_tokens += estimated_tokens

        # 如果在 token 限制内，直接使用
        if total_tokens <= max_tokens:
            final_batches.append(batch)
        else:
            # 否则进一步拆分为更小的批次
            import logging

            logging.warning(
                f"批次 token 数 ({total_tokens}) 超过限制 ({max_tokens})，"
                f"将 {len(batch)} 句拆分为更小的批次"
            )
            current_sub_batch = []
            current_tokens = 0

            for seg in batch:
                sentence = seg.get("sentence", "")
                estimated_tokens = int(calculator.count_tokens(sentence) * 1.5) + 20

                if current_tokens + estimated_tokens > max_tokens and current_sub_batch:
                    final_batches.append(current_sub_batch)
                    current_sub_batch = [seg]
                    current_tokens = estimated_tokens
                else:
                    current_sub_batch.append(seg)
                    current_tokens += estimated_tokens

            if current_sub_batch:
                final_batches.append(current_sub_batch)

    return final_batches
