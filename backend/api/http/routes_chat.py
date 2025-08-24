# -*- coding: utf-8 -*-
"""
聊天 HTTP 路由：
- POST /chat/text: 输入 {"prompt": str}，返回 {"content": str}
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body

from backend.services.chat_service import chat_text_once

router = APIRouter(prefix="/chat", tags=["chat"]) 


@router.post("/text")
def http_chat_text(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    prompt = str(payload.get("prompt", ""))
    if not prompt:
        return {"error": "prompt is required"}
    content = chat_text_once(prompt)
    return {"content": content}
