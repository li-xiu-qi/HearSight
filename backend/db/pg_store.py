# -*- coding: utf-8 -*-
"""PostgreSQL 存储主入口，聚合各功能模块"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .job_store import (
    claim_next_pending_job,
    create_job,
    finish_job_failed,
    finish_job_success,
    get_job,
    init_job_table,
    list_jobs,
    update_job_result,
    update_job_status,
)
from .transcript_crud import (
    delete_transcript,
    get_summaries,
    get_transcript_by_id,
    get_translations,
    save_summaries,
    save_transcript,
    save_translations,
    update_transcript,
)
from .transcript_init import init_transcript_table
from .transcript_query import (
    count_transcripts,
    get_latest_transcript,
    list_transcripts_meta,
)


def init_db(db_url: Optional[str] = None) -> None:
    """初始化 Postgres 中需要的表和索引。"""
    init_transcript_table(db_url)
    init_job_table(db_url)


__all__ = [
    # 初始化
    "init_db",
    # 转写相关
    "save_transcript",
    "update_transcript",
    "get_latest_transcript",
    "list_transcripts_meta",
    "count_transcripts",
    "get_transcript_by_id",
    "delete_transcript",
    # 总结相关
    "save_summaries",
    "get_summaries",
    # 翻译相关
    "save_translations",
    "get_translations",
    # 任务相关
    "create_job",
    "get_job",
    "list_jobs",
    "claim_next_pending_job",
    "finish_job_success",
    "finish_job_failed",
    "update_job_result",
    "update_job_status",
]
