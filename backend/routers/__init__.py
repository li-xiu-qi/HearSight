# -*- coding: utf-8 -*-
"""路由模块统一入口"""

from .download_router import router as download_router
from .asr_router import router as asr_router
from .transcript_router import router as transcript_router
from .job_router import router as job_router
from .chat_router import router as chat_router
from .thumbnail_router import router as thumbnail_router

__all__ = [
    "download_router",
    "asr_router",
    "transcript_router",
    "job_router",
    "chat_router",
    "thumbnail_router",
]