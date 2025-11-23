# -*- coding: utf-8 -*-
"""聊天路由模块"""

from fastapi import APIRouter

from .summarize_router import router as summarize_router
from .chat_conversation_router import router as chat_conversation_router
from .messages_router import router as messages_router
from .chat_session_router import router as chat_session_router


router = APIRouter(tags=["chat"])

# 包含所有子路由
router.include_router(summarize_router)
router.include_router(chat_conversation_router)
router.include_router(messages_router)
router.include_router(chat_session_router)