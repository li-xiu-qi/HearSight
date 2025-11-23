# -*- coding: utf-8 -*-
"""聊天会话相关的路由"""

from fastapi import APIRouter, HTTPException, Request

from backend.db.chat_session_crud import (
    create_chat_session, get_chat_sessions, get_chat_session,
    update_chat_session_title, delete_chat_session
)
from backend.db.chat_message_crud import save_chat_messages, get_chat_messages, clear_chat_messages
from .models import (
    CreateChatSessionRequest, CreateChatSessionResponse,
    GetChatSessionsResponse, GetChatSessionResponse,
    UpdateChatSessionTitleRequest, UpdateChatSessionTitleResponse,
    SessionSaveChatMessagesRequest, SessionSaveChatMessagesResponse,
    SessionGetChatMessagesResponse, SessionClearChatMessagesResponse
)


router = APIRouter()


@router.post("/chat-sessions")
def api_create_chat_session(
    payload: CreateChatSessionRequest, request: Request
) -> CreateChatSessionResponse:
    """创建新的chat会话。

    请求 body 字段：
        - title: str (可选) 会话标题

    返回：{"success": bool, "session_id": int}
    """
    db_url = request.app.state.db_url
    title = payload.title

    try:
        print(f"[DEBUG] api_create_chat_session: payload.title={title!r}")
        print(f"[DEBUG] api_create_chat_session: db_url={db_url}")
        session_id = create_chat_session(db_url, title)
        if session_id:
            return {
                "success": True,
                "session_id": session_id,
            }
        else:
            raise HTTPException(status_code=500, detail="创建会话失败")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create chat session: {str(e)}"
        )


@router.get("/chat-sessions")
def api_get_chat_sessions(
    request: Request, limit: int = 50, offset: int = 0
) -> GetChatSessionsResponse:
    """获取chat会话列表。

    返回：{"sessions": List[Dict]}
    """
    db_url = request.app.state.db_url

    try:
        sessions = get_chat_sessions(db_url, limit, offset)
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get chat sessions: {str(e)}"
        )


@router.get("/chat-sessions/{session_id}")
def api_get_chat_session(session_id: int, request: Request) -> GetChatSessionResponse:
    """获取单个chat会话。

    返回：{"session": Dict | null}
    """
    db_url = request.app.state.db_url

    try:
        session = get_chat_session(db_url, session_id)
        return {"session": session}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get chat session: {str(e)}"
        )


@router.put("/chat-sessions/{session_id}/title")
def api_update_chat_session_title(
    session_id: int, payload: UpdateChatSessionTitleRequest, request: Request
) -> UpdateChatSessionTitleResponse:
    """更新chat会话标题。

    请求 body 字段：
        - title: str 会话标题

    返回：{"success": bool, "message": str}
    """
    db_url = request.app.state.db_url
    title = payload.title

    try:
        success = update_chat_session_title(db_url, session_id, title)
        if success:
            return {
                "success": True,
                "message": "会话标题已更新",
            }
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update chat session title: {str(e)}"
        )


@router.delete("/chat-sessions/{session_id}")
def api_delete_chat_session(session_id: int, request: Request) -> dict:
    """删除chat会话。

    返回：{"success": bool, "message": str}
    """
    db_url = request.app.state.db_url

    try:
        success = delete_chat_session(db_url, session_id)
        if success:
            return {
                "success": True,
                "message": "会话已删除",
            }
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete chat session: {str(e)}"
        )


@router.post("/chat-sessions/{session_id}/messages")
def api_save_chat_messages(
    session_id: int, payload: SessionSaveChatMessagesRequest, request: Request
) -> SessionSaveChatMessagesResponse:
    """保存chat消息。

    请求 body 字段：
        - messages: List[Dict] chat消息列表

    返回：{"success": bool, "message": str}
    """
    db_url = request.app.state.db_url
    messages = payload.messages
    # 调试打印：显示请求信息
    print(f"[DEBUG] api_save_chat_messages called: session_id={session_id}, payload_messages_count={len(messages) if messages else 0}")

    if not messages or not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="messages (list) is required")

    # 先检查会话是否存在，避免将数据库错误误报为 404
    try:
        # 打印尝试查询会话与 db_url
        print(f"[DEBUG] checking session existence for id={session_id}, db_url={db_url}")
        session = get_chat_session(db_url, session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check chat session existence: {e}")

    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    try:
        print(f"[DEBUG] calling save_chat_messages for session_id={session_id}")
        success = save_chat_messages(db_url, session_id, messages)
        if success:
            # 打印返回body以便调试客户端是否能收到
            resp = {"success": True, "message": "chat消息已保存"}
            print(f"[DEBUG] api_save_chat_messages response: {resp}")
            return resp
        else:
            # 保存失败（例如数据库异常或其他原因），区分为 500
            raise HTTPException(status_code=500, detail="保存 chat 消息失败（DB error）")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save chat messages: {str(e)}"
        )


@router.get("/chat-sessions/{session_id}/messages")
def api_get_chat_messages(session_id: int, request: Request) -> SessionGetChatMessagesResponse:
    """获取chat消息。

    返回：{"messages": List[Dict] | null, "has_messages": bool}
    """
    db_url = request.app.state.db_url

    try:
        messages = get_chat_messages(db_url, session_id)
        return {
            "messages": messages,
            "has_messages": messages is not None and len(messages) > 0,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get chat messages: {str(e)}"
        )


@router.delete("/chat-sessions/{session_id}/messages")
def api_clear_chat_messages(session_id: int, request: Request) -> SessionClearChatMessagesResponse:
    """清空chat消息。

    返回：{"success": bool, "message": str}
    """
    db_url = request.app.state.db_url

    try:
        success = clear_chat_messages(db_url, session_id)
        if success:
            return {
                "success": True,
                "message": "chat消息已清空",
            }
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to clear chat messages: {str(e)}"
        )