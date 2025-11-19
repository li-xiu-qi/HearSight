# -*- coding: utf-8 -*-
"""
集中类型定义，避免各处重复：
- Segment: 语音转写后的句级片段（不含 spk_id）
- SummaryItem: 汇总输出项
"""
from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import TypedDict


class Segment(TypedDict, total=False):
    index: int
    sentence: str
    start_time: float
    end_time: float
    translation: Optional[Dict[str, str]]


class SummaryItem(TypedDict):
    topic: str
    summary: str
    start_time: float
    end_time: float
