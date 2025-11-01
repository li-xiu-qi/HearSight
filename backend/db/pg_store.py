# -*- coding: utf-8 -*-
"""PostgreSQL 存储主入口，聚合各功能模块"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .transcript_init import init_transcript_table
from .transcript_crud import (
    save_transcript,
    update_transcript,
    get_transcript_by_id,
    delete_transcript,
)
from .transcript_query import (
    get_latest_transcript,
    list_transcripts_meta,
    count_transcripts,
)
from .job_store import (
    init_job_table,
    create_job,
    get_job,
    list_jobs,
    claim_next_pending_job,
    finish_job_success,
    finish_job_failed,
    update_job_result,
    update_job_status,
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
