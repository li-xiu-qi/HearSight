# -*- coding: utf-8 -*-
"""翻译相关的路由"""

from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from typing_extensions import TypedDict

from backend.db.transcript_crud import get_translations
from backend.services.translate_service import (get_translate_progress,
                                                start_translate_task)
from backend.services.transcript_service import get_transcript_async


# 翻译相关的数据模型
class StartTranslateResponse(TypedDict):
    """开始翻译响应数据结构"""

    status: str  # 状态
    transcript_id: int  # 转写记录ID


class GetTranslationsResponse(TypedDict):
    """获取翻译结果响应数据结构"""

    translations: Optional[Dict[str, List[Any]]]  # 翻译结果字典
    has_translations: bool  # 是否有翻译结果


class TranscriptTranslateRequest(BaseModel):
    target_lang_code: str = "zh"
    source_lang_code: Optional[str] = None
    confirmed: bool = True
    max_tokens: int = 4096
    source_lang_display_name: Optional[str] = None
    target_lang_display_name: Optional[str] = None
    force_retranslate: bool = False


router = APIRouter()


@router.post("/transcripts/{transcript_id}/translate")
async def api_translate_transcript(
    transcript_id: int, request: Request, body: TranscriptTranslateRequest
) -> StartTranslateResponse:
    """翻译转写内容。后台异步翻译，使用SSE流式推送进度。

    请求体: {
        "target_language": "zh" | "en",
        "confirmed": bool
    }

    返回: { "status": "started", "transcript_id": int }
    """
    db_url = request.app.state.db_url

    data = await get_transcript_async(db_url, transcript_id)
    if not data:
        raise HTTPException(
            status_code=404, detail=f"transcript not found: {transcript_id}"
        )

    segments = data.get("segments", [])
    if not segments:
        raise HTTPException(status_code=400, detail="No segments to translate")

    return await start_translate_task(
        transcript_id,
        segments,
        body.target_lang_code,
        body.max_tokens,
        body.source_lang_code or "",
        body.source_lang_display_name or "",
        body.target_lang_display_name or "",
        force_retranslate=body.force_retranslate,
    )


@router.get("/transcripts/{transcript_id}/translate/stream")
async def api_translate_progress_stream(
    transcript_id: int, request: Request
):
    """SSE流式获取翻译进度。

    返回实时翻译进度事件流。
    """
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    from backend.services.translate_service import get_translate_progress

    async def generate():
        # 立即发送当前进度状态
        try:
            initial_progress = get_translate_progress(transcript_id)
            initial_data = {
                "type": "progress",
                "status": initial_progress["status"],
                "progress": initial_progress["progress"],
                "translated_count": initial_progress["translated_count"],
                "total_count": initial_progress["total_count"],
                "message": initial_progress["message"]
            }
            yield f"data: {json.dumps(initial_data)}\n\n"

            # 如果已经完成或出错，立即结束
            if initial_progress["status"] in ["completed", "error"]:
                if initial_progress["status"] == "completed":
                    initial_data["type"] = "complete"
                    initial_data["is_complete"] = True
                else:
                    initial_data["type"] = "error"
                yield f"data: {json.dumps(initial_data)}\n\n"
                return

        except Exception as e:
            error_data = {
                "type": "error",
                "message": f"获取初始进度失败: {str(e)}"
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            return

        last_progress = initial_progress
        while True:
            try:
                await asyncio.sleep(1)  # 每秒检查一次进度
                progress = get_translate_progress(transcript_id)

                # 只在进度发生变化时发送
                if progress != last_progress:
                    last_progress = progress
                    data = {
                        "type": "progress",
                        "status": progress["status"],
                        "progress": progress["progress"],
                        "translated_count": progress["translated_count"],
                        "total_count": progress["total_count"],
                        "message": progress["message"]
                    }

                    # 如果完成或出错，发送最终事件并结束流
                    if progress["status"] in ["completed", "error"]:
                        if progress["status"] == "completed":
                            data["type"] = "complete"
                            data["is_complete"] = True
                        else:
                            data["type"] = "error"
                        yield f"data: {json.dumps(data)}\n\n"
                        break
                    else:
                        yield f"data: {json.dumps(data)}\n\n"

            except Exception as e:
                error_data = {
                    "type": "error",
                    "message": f"获取进度失败: {str(e)}"
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/transcripts/{transcript_id}/translations")
async def api_get_translations(
    transcript_id: int, request: Request
) -> GetTranslationsResponse:
    """获取已保存的翻译结果。

    返回: {
        "translations": Dict[str, List] | null,
        "has_translations": bool
    }
    """
    db_url = request.app.state.db_url

    try:
        translations = get_translations(db_url, transcript_id)
        return {
            "translations": translations,
            "has_translations": translations is not None and len(translations) > 0,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get translations: {str(e)}"
        )