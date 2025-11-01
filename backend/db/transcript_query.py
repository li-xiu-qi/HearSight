# -*- coding: utf-8 -*-
"""转写记录查询模块"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from psycopg2.extras import RealDictCursor

from .conn_utils import connect_db


def get_latest_transcript(db_url: Optional[str], media_path: str) -> Optional[List[Dict[str, Any]]]:
    """获取指定媒体文件的最新转写记录。

    Args:
        db_url: 数据库连接 URL
        media_path: 媒体文件路径

    Returns:
        转写片段列表，如果不存在返回 None
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT segments_json FROM transcripts
                    WHERE media_path = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (media_path,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                try:
                    return json.loads(row[0])
                except Exception:
                    return None
    finally:
        conn.close()


def list_transcripts_meta(db_url: Optional[str], limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """列出转写记录的元信息（不包含大字段），按 id 倒序。

    Args:
        db_url: 数据库连接 URL
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        转写记录元信息列表，包含 id、media_path、created_at、segment_count
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, media_path, segments_json, created_at
                    FROM transcripts
                    ORDER BY id DESC
                    LIMIT %s OFFSET %s
                    """,
                    (int(limit), int(offset)),
                )
                rows = cur.fetchall()
                items: List[Dict[str, Any]] = []
                for r in rows:
                    rid = r["id"]
                    media_path = r["media_path"]
                    seg_json = r["segments_json"]
                    created_at = r["created_at"]
                    try:
                        segs = json.loads(seg_json)
                        seg_count = len(segs) if isinstance(segs, list) else 0
                    except Exception:
                        seg_count = 0
                    items.append({
                        "id": int(rid),
                        "media_path": str(media_path),
                        "created_at": str(created_at),
                        "segment_count": int(seg_count),
                    })
                return items
    finally:
        conn.close()


def count_transcripts(db_url: Optional[str]) -> int:
    """获取转写记录总数。

    Args:
        db_url: 数据库连接 URL

    Returns:
        转写记录总数
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM transcripts")
                row = cur.fetchone()
                return int(row[0]) if row and row[0] is not None else 0
    finally:
        conn.close()
