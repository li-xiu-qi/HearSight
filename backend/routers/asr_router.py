# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from backend.audio2text.asr_sentence_segments import process as asr_process
from backend.db.pg_store import save_transcript

router = APIRouter(prefix="/api", tags=["asr"])


@router.post("/asr/segments")
def api_asr_segments(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    """处理音频文件并生成句子片段"""
    audio_path = payload.get("audio_path")
    if not audio_path:
        raise HTTPException(status_code=400, detail="audio_path is required")

    p = Path(audio_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"audio not found: {audio_path}")

    segs = asr_process(str(p))
    # 保存到数据库（使用 postgres dsn 或由 pg_store 从环境读取）
    db_url = request.app.state.db_url
    
    # 检测媒体类型
    media_ext = p.suffix.lower()
    audio_extensions = {'.m4a', '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'}
    media_type = 'audio' if media_ext in audio_extensions else 'video'
    
    transcript_id = save_transcript(db_url, str(p.resolve()), segs, media_type)
    return {"segments": segs, "transcript_id": transcript_id}
