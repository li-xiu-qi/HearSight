# -*- coding: utf-8 -*-
"""
转录和总结相关的数据模式定义
- Segment: 语音转写后的句级片段
- SummaryItem: 总结项目
"""
from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import TypedDict


class Segment(TypedDict, total=False):
    """语音转写后的句级片段（包含说话人信息，允许额外字段被忽略）"""
    index: int
    sentence: str
    start_time: float
    end_time: float
    spk_id: Optional[str]  # 说话人ID，可为空
    translation: Optional[Dict[str, str]]


class SummaryItem(TypedDict):
    """总结项：包含主题标题、内容和时间范围"""
    topic: str
    summary: str
    start_time: float
    end_time: float
