
# -*- coding: utf-8 -*-
"""任务队列基础存储模块"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from .conn_utils import connect_db


def init_job_table(db_url: Optional[str] = None) -> None:
    """初始化任务表和索引。"""
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS jobs (
                        id SERIAL PRIMARY KEY,
                        url TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        created_at TIMESTAMP NOT NULL DEFAULT (now()),
                        started_at TIMESTAMP,
                        finished_at TIMESTAMP,
                        result_json TEXT,
                        error TEXT,
                        celery_task_id VARCHAR(255)
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_jobs_status_created
                    ON jobs(status, created_at DESC);
                    """
                )
                # 添加celery_task_id列（如果还不存在）
                cur.execute(
                    """
                    ALTER TABLE IF EXISTS jobs
                    ADD COLUMN IF NOT EXISTS celery_task_id VARCHAR(255);
                    """
                )
    finally:
        conn.close()


def create_job(db_url: Optional[str], url: str) -> int:
    """创建新任务。

    Args:
        db_url: 数据库连接 URL
        url: 任务 URL

    Returns:
        新创建的任务 ID
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO jobs (url, status) VALUES (%s, %s) RETURNING id",
                    (url, "pending"),
                )
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("Failed to insert job")
                return int(row[0])
    finally:
        conn.close()


def get_job(db_url: Optional[str], job_id: int) -> Optional[Dict[str, Any]]:
    """根据 ID 获取任务。

    Args:
        db_url: 数据库连接 URL
        job_id: 任务 ID

    Returns:
        任务详情，如果不存在返回 None
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, url, status, created_at, started_at, finished_at, result_json, error, celery_task_id FROM jobs WHERE id = %s",
                    (int(job_id),),
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
                    "created_at": str(row["created_at"]) if row["created_at"] else None,
                    "started_at": str(row["started_at"]) if row["started_at"] else None,
                    "finished_at": (
                        str(row["finished_at"]) if row["finished_at"] else None
                    ),
                    "result": result,
                    "error": str(row["error"]) if row["error"] else None,
                    "celery_task_id": str(row["celery_task_id"]) if row["celery_task_id"] else None,
                }
    finally:
        conn.close()


def list_jobs(
    db_url: Optional[str],
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """列出任务。

    Args:
        db_url: 数据库连接 URL
        status: 按状态筛选，为空则列出所有任务
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        任务列表
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if status:
                    cur.execute(
                        "SELECT id, url, status, created_at, started_at, finished_at, result_json, error, celery_task_id FROM jobs WHERE status = %s ORDER BY id DESC LIMIT %s OFFSET %s",
                        (status, int(limit), int(offset)),
                    )
                else:
                    cur.execute(
                        "SELECT id, url, status, created_at, started_at, finished_at, result_json, error, celery_task_id FROM jobs ORDER BY id DESC LIMIT %s OFFSET %s",
                        (int(limit), int(offset)),
                    )
                rows = cur.fetchall()
                items: List[Dict[str, Any]] = []
                for r in rows:
                    try:
                        result = (
                            json.loads(r["result_json"]) if r["result_json"] else None
                        )
                    except Exception:
                        result = None
                    items.append(
                        {
                            "id": int(r["id"]),
                            "url": str(r["url"]),
                            "status": str(r["status"]),
                            "created_at": (
                                str(r["created_at"]) if r["created_at"] else None
                            ),
                            "started_at": (
                                str(r["started_at"]) if r["started_at"] else None
                            ),
                            "finished_at": (
                                str(r["finished_at"]) if r["finished_at"] else None
                            ),
                            "result": result,
                            "error": str(r["error"]) if r["error"] else None,
                            "celery_task_id": str(r["celery_task_id"]) if r["celery_task_id"] else None,
                        }
                    )
                return items
    finally:
        conn.close()