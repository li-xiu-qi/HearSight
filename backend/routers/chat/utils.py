# -*- coding: utf-8 -*-
"""聊天路由的工具函数"""

import os
from typing import Any, Dict

from fastapi import HTTPException

from backend.config import settings


def get_llm_config(payload: Dict[str, Any]) -> tuple[str, str, str]:
    """获取LLM配置，优先从payload，否则从settings"""
    api_key = payload.get("api_key") or settings.llm_provider_api_key
    base_url = payload.get("base_url") or settings.llm_provider_base_url
    model = payload.get("model") or settings.llm_model
    
    if not api_key or not base_url or not model:
        raise HTTPException(
            status_code=400,
            detail="api_key, base_url and model are required (either in payload or config/env)",
        )
    return api_key, base_url, model