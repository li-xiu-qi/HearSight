# -*- coding: utf-8 -*-
"""任务队列存储模块"""
from __future__ import annotations

import json
from pathlib import Path
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



def finish_job_success(
    db_url: Optional[str], job_id: int, result: Dict[str, Any]
) -> None:
    """标记任务成功完成。

    Args:
        db_url: 数据库连接 URL
        job_id: 任务 ID
        result: 任务结果数据
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE jobs SET status = 'success', finished_at = now(), result_json = %s WHERE id = %s",
                    (json.dumps(result, ensure_ascii=False), int(job_id)),
                )
    finally:
        conn.close()


def finish_job_failed(db_url: Optional[str], job_id: int, error: str) -> None:
    """标记任务失败。

    Args:
        db_url: 数据库连接 URL
        job_id: 任务 ID
        error: 错误信息
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE jobs SET status = 'failed', finished_at = now(), error = %s WHERE id = %s",
                    (error, int(job_id)),
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


def update_job_result(
    db_url: Optional[str],
    job_id: int,
    patch: Dict[str, Any],
    status: Optional[str] = None,
) -> None:
    """合并写入任务结果，可选同时更新状态。

    Args:
        db_url: 数据库连接 URL
        job_id: 任务 ID
        patch: 要合并的结果数据
        status: 可选的新状态
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT result_json FROM jobs WHERE id = %s",
                    (int(job_id),),
                )
                row = cur.fetchone()
                current: Dict[str, Any]
                if row:
                    result_json = row.get("result_json")
                    if result_json and result_json.strip():
                        try:
                            current = json.loads(result_json)
                            if not isinstance(current, dict):
                                current = {}
                        except Exception:
                            current = {}
                    else:
                        current = {}
                else:
                    current = {}

                current.update(patch or {})
                if status:
                    cur.execute(
                        "UPDATE jobs SET result_json = %s, status = %s WHERE id = %s",
                        (json.dumps(current, ensure_ascii=False), status, int(job_id)),
                    )
                else:
                    cur.execute(
                        "UPDATE jobs SET result_json = %s WHERE id = %s",
                        (json.dumps(current, ensure_ascii=False), int(job_id)),
                    )
    finally:
        conn.close()


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


def update_job_result_paths(
    db_url: Optional[str], old_basename: str, new_basename: str, static_dir_path: str
) -> int:
    """更新所有相关任务的result中的文件路径信息。

    Args:
        db_url: 数据库连接 URL
        old_basename: 旧文件名
        new_basename: 新文件名
        static_dir_path: 静态文件目录的绝对路径

    Returns:
        更新的任务数量
    """
    conn = connect_db(db_url)
    updated_count = 0
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 查找所有包含该文件的任务
                cur.execute(
                    "SELECT id, result_json FROM jobs WHERE result_json LIKE %s",
                    (f"%{old_basename}%",),
                )
                rows = cur.fetchall()

                for row in rows:
                    job_id = row["id"]
                    result_json = row.get("result_json")
                    if not result_json:
                        continue

                    try:
                        result = json.loads(result_json)
                        if not isinstance(result, dict):
                            continue

                        # 更新basename
                        if result.get("basename") == old_basename:
                            result["basename"] = new_basename
                            result["static_url"] = f"/static/{new_basename}"

                            # 更新media_path
                            old_media_path = result.get("media_path", "")
                            if old_basename in old_media_path:
                                result["media_path"] = str(
                                    Path(static_dir_path) / new_basename
                                )

                            # 保存更新后的result
                            cur.execute(
                                "UPDATE jobs SET result_json = %s WHERE id = %s",
                                (json.dumps(result, ensure_ascii=False), job_id),
                            )
                            updated_count += 1
                    except Exception as e:
                        # 单个任务更新失败不影响其他任务
                        continue

    finally:
        conn.close()

    return updated_count
