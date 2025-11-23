# -*- coding: utf-8 -*-
"""任务队列结果存储模块"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

from .conn_utils import connect_db


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