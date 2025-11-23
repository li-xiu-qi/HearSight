# -*- coding: utf-8 -*-
"""转写记录 CRUD 操作模块"""

# 为保持向后兼容性，从各个子模块导入所有函数
from .transcript_base_crud import (
    save_transcript,
    get_transcript_by_id,
    update_transcript,
    update_transcript_audio_path,
    delete_transcript,
    get_all_transcript_ids
)

from .transcript_summary_crud import (
    save_summaries,
    get_summaries
)

from .transcript_translation_crud import (
    save_translations,
    get_translations
)

from .transcript_chat_crud import (
    save_chat_messages,
    get_chat_messages,
    clear_chat_messages
)

__all__ = [
    "save_transcript",
    "get_transcript_by_id",
    "update_transcript",
    "update_transcript_audio_path",
    "delete_transcript",
    "get_all_transcript_ids",
    "save_summaries",
    "get_summaries",
    "save_translations",
    "get_translations",
    "save_chat_messages",
    "get_chat_messages",
    "clear_chat_messages"
]
