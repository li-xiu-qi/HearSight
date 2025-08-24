# -*- coding: utf-8 -*-
"""
ASR 服务：封装句级识别，统一输出 Segment 列表（不含 spk_id）。
"""
from __future__ import annotations

from typing import List

from backend.utils.typing_defs import Segment
from backend.audio2text.asr_sentence_segments import process as asr_process


def asr_segments(audio_path: str) -> List[Segment]:
    """调用底层 ASR，转换为统一的 Segment 列表。
    - 去除 spk_id 字段；
    - index 保持底层顺序编号；
    - 时间戳保留为毫秒（float）。
    """
    raw = asr_process(audio_path)
    segs: List[Segment] = []
    for item in raw:
        segs.append(
            Segment(
                index=int(item.get("index", len(segs) + 1)),
                sentence=str(item.get("sentence", "")),
                start_time=float(item.get("start_time", 0.0)),
                end_time=float(item.get("end_time", 0.0)),
            )
        )
    return segs
