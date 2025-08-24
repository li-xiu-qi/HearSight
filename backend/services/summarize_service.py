# -*- coding: utf-8 -*-
"""
总结服务：对 text_process.summarize 进行薄封装，
- 从 configs.settings 读取默认配置；
- 对外暴露一个简单函数 summarize_once。
"""
from __future__ import annotations

from typing import List

from backend.utils.typing_defs import Segment, SummaryItem
from backend.text_process.summarize import summarize_segments
from config import get_config


def summarize_once(segments: List[Segment]) -> List[SummaryItem]:
    config = get_config() 
    
    openai_config = config.get("chat_server").get("openai")
    api_key = openai_config.get("api_key")
    base_url = openai_config.get("base_url")
    model = openai_config.get("chat_model")
    max_tokens = openai_config.get("chat_max_tokens")


    return summarize_segments(
        segments=segments,
        api_key=api_key,
        base_url=base_url,
        model=model,
        max_tokens=max_tokens,
    )
