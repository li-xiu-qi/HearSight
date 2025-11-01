# -*- coding: utf-8 -*-
"""转写记录 CRUD 操作模块"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from .conn_utils import connect_db


def save_transcript(db_url: Optional[str], media_path: str, segments: List[Dict[str, Any]]) -> int:
    """保存转写记录。

    Args:
        db_url: 数据库连接 URL
        media_path: 媒体文件路径
        segments: 转写片段列表

    Returns:
        新创建的转写记录 ID
    """
    conn = connect_db(db_url)
    data = json.dumps(segments, ensure_ascii=False)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO transcripts (media_path, segments_json) VALUES (%s, %s) RETURNING id",
                    (media_path, data),
                )
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("Failed to insert transcript")
                return int(row[0])
    finally:
        conn.close()


def update_transcript(db_url: Optional[str], transcript_id: int, segments: List[Dict[str, Any]]) -> bool:
    """更新转写记录。

    Args:
        db_url: 数据库连接 URL
        transcript_id: 转写记录 ID
        segments: 新的转写片段列表

    Returns:
        是否更新成功
    """
    conn = connect_db(db_url)
    data = json.dumps(segments, ensure_ascii=False)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE transcripts SET segments_json = %s WHERE id = %s",
                    (data, transcript_id),
                )
                return cur.rowcount > 0
    finally:
        conn.close()


def get_transcript_by_id(db_url: Optional[str], transcript_id: int) -> Optional[Dict[str, Any]]:
    """根据 ID 获取转写记录。

    Args:
        db_url: 数据库连接 URL
        transcript_id: 转写记录 ID

    Returns:
        转写记录详情，如果不存在返回 None
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, media_path, segments_json, created_at
                    FROM transcripts
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (int(transcript_id),),
                )
                row = cur.fetchone()
                if not row:
                    return None
                try:
                    segs = json.loads(row["segments_json"])
                except Exception:
                    segs = []
                return {
                    "id": int(row["id"]),
                    "media_path": str(row["media_path"]),
                    "created_at": str(row["created_at"]),
                    "segments": segs,
                }
    finally:
        conn.close()


def update_transcript_media_path(db_url: Optional[str], old_media_path: str, new_media_path: str) -> int:
    """更新转写记录的media_path。

    Args:
        db_url: 数据库连接 URL
        old_media_path: 旧的媒体文件路径
        new_media_path: 新的媒体文件路径

    Returns:
        更新的记录数量
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE transcripts SET media_path = %s WHERE media_path = %s",
                    (new_media_path, old_media_path),
                )
                return cur.rowcount
    finally:
        conn.close()


def delete_transcript(db_url: Optional[str], transcript_id: int) -> bool:
    """删除指定的转写记录。

    Args:
        db_url: 数据库连接 URL
        transcript_id: 转写记录 ID

    Returns:
        如果删除成功返回 True，记录不存在返回 False
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM transcripts WHERE id = %s",
                    (int(transcript_id),),
                )
                return cur.rowcount > 0
    finally:
        conn.close()
