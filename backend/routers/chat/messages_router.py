# -*- coding: utf-8 -*-
"""消息和总结保存相关的路由"""

from fastapi import APIRouter, HTTPException, Request

from backend.db.transcript_crud import (
    clear_chat_messages, get_chat_messages,
    get_summaries, save_chat_messages, save_summaries
)
from .models import (
    SaveSummariesRequest, SaveSummariesResponse, GetSummariesResponse,
    SaveChatMessagesRequest, SaveChatMessagesResponse, GetChatMessagesResponse,
    ClearChatMessagesResponse
)


router = APIRouter()


@router.post("/transcripts/{transcript_id}/summaries")
def api_save_summaries(
    transcript_id: int, payload: SaveSummariesRequest, request: Request
) -> SaveSummariesResponse:
    """保存生成的总结到数据库。

    请求 body 字段：
        - summaries: List[SummaryItem] （必需）总结内容

    返回：{"success": bool, "message": str, "saved": bool}
    """
    db_url = request.app.state.db_url
    summaries = payload.summaries

    if not summaries or not isinstance(summaries, list):
        raise HTTPException(status_code=400, detail="summaries (list) is required")

    try:
        saved = save_summaries(db_url, transcript_id, summaries)
        return {
            "success": True,
            "message": "总结已保存" if saved else "总结已存在",
            "saved": saved,
            "transcript_id": transcript_id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save summaries: {str(e)}"
        )


@router.get("/transcripts/{transcript_id}/summaries")
def api_get_summaries(transcript_id: int, request: Request) -> GetSummariesResponse:
    """获取已保存的总结。

    返回：{"summaries": List[Dict] | null, "has_summaries": bool}
    """
    db_url = request.app.state.db_url

    try:
        summaries = get_summaries(db_url, transcript_id)
        return {
            "summaries": summaries,
            "has_summaries": summaries is not None and len(summaries) > 0,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get summaries: {str(e)}"
        )


@router.post("/transcripts/{transcript_id}/chat-messages")
def api_save_chat_messages(
    transcript_id: int, payload: SaveChatMessagesRequest, request: Request
) -> SaveChatMessagesResponse:
    """保存chat消息到数据库。

    请求 body 字段：
        - messages: List[Dict] （必需）chat消息列表

    返回：{"success": bool, "message": str}
    """
    db_url = request.app.state.db_url
    messages = payload.messages

    if not messages or not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="messages (list) is required")

    try:
        success = save_chat_messages(db_url, transcript_id, messages)
        if success:
            return {
                "success": True,
                "message": "chat消息已保存",
                "transcript_id": transcript_id,
            }
        else:
            raise HTTPException(
                status_code=404, detail=f"Transcript {transcript_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save chat messages: {str(e)}"
        )


@router.get("/transcripts/{transcript_id}/chat-messages")
def api_get_chat_messages(
    transcript_id: int, request: Request
) -> GetChatMessagesResponse:
    """获取已保存的chat消息。

    返回：{"messages": List[Dict] | null, "has_messages": bool}
    """
    db_url = request.app.state.db_url

    try:
        messages = get_chat_messages(db_url, transcript_id)
        return {
            "messages": messages,
            "has_messages": messages is not None and len(messages) > 0,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get chat messages: {str(e)}"
        )


@router.delete("/transcripts/{transcript_id}/chat-messages")
def api_clear_chat_messages(
    transcript_id: int, request: Request
) -> ClearChatMessagesResponse:
    """清空chat消息。

    返回：{"success": bool, "message": str}
    """
    db_url = request.app.state.db_url

    try:
        success = clear_chat_messages(db_url, transcript_id)
        if success:
            return {
                "success": True,
                "message": "chat消息已清空",
                "transcript_id": transcript_id,
            }
        else:
            raise HTTPException(
                status_code=404, detail=f"Transcript {transcript_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to clear chat messages: {str(e)}"
        )