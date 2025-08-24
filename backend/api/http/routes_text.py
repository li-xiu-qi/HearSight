# -*- coding: utf-8 -*-
"""
文本总结 HTTP 路由：
- POST /text/summarize: 输入 {"segments": List[Segment]}，返回 {"items": List[SummaryItem]}
说明：遵循最小实现，不做过度 try/except。
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Body

from backend.services.summarize_service import summarize_once

router = APIRouter(prefix="/text", tags=["text"]) 


@router.post("/summarize")
def http_text_summarize(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    segments: List[Dict[str, Any]] = list(payload.get("segments") or [])
    items = summarize_once(segments)  # 直接复用服务层，按项目规则：最小实现
    return {"items": items}
