# -*- coding: utf-8 -*-
"""
ASR HTTP 路由：
- POST /asr/segments: 输入 {"audio_path": str}，返回 {"segments": List[Segment]}
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body

from backend.services.asr_service import asr_segments

router = APIRouter(prefix="/asr", tags=["asr"])


@router.post("/segments")
def http_asr_segments(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    audio_path = str(payload.get("audio_path", "")).strip()
    if not audio_path:
        return {"error": "audio_path is required"}
    segs = asr_segments(audio_path)
    return {"segments": segs}
