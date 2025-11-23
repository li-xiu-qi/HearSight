# -*- coding: utf-8 -*-
"""任务队列状态存储模块"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

import psycopg2

from .conn_utils import connect_db


def update_job_status(db_url: Optional[str], job_id: int, status: str) -> None:
    """更新任务状态。

    Args:
        db_url: 数据库连接 URL
        job_id: 任务 ID
        status: 新状态
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE jobs SET status = %s WHERE id = %s",
                    (status, int(job_id)),
                )
    finally:
        conn.close()


def update_job_celery_task_id(db_url: Optional[str], job_id: int, celery_task_id: str) -> None:
    """保存Celery任务ID到job记录。

    Args:
        db_url: 数据库连接 URL
        job_id: 任务 ID
        celery_task_id: Celery任务 ID
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE jobs SET celery_task_id = %s WHERE id = %s",
                    (celery_task_id, int(job_id)),
                )
    finally:
        conn.close()


def check_duplicate_url(db_url: Optional[str], url: str) -> Optional[Dict[str, Any]]:
    """检查是否存在已成功下载的相同URL。

    Args:
        db_url: 数据库连接 URL
        url: 要检查的URL

    Returns:
        如果存在成功下载的记录返回该任务信息，否则返回None
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, url, status, finished_at, result_json FROM jobs WHERE url = %s AND status = %s ORDER BY finished_at DESC LIMIT 1",
                    (url, "success"),
                )
                row = cur.fetchone()
                if not row:
                    return None
                try:
                    result = (
                        json.loads(row["result_json"]) if row["result_json"] else None
                    )
                except Exception:
                    result = None
                return {
                    "id": int(row["id"]),
                    "url": str(row["url"]),
                    "status": str(row["status"]),
                    "finished_at": (
                        str(row["finished_at"]) if row["finished_at"] else None
                    ),
                    "result": result,
                }
    finally:
        conn.close()