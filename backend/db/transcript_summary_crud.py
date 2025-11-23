# -*- coding: utf-8 -*-
"""转写记录总结 CRUD 操作模块"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from .conn_utils import connect_db


def save_summaries(
    db_url: Optional[str], transcript_id: int, summaries: List[Dict[str, Any]]
) -> bool:
    """保存总结到数据库。

    Args:
        db_url: 数据库连接 URL
        transcript_id: 转写记录 ID
        summaries: 总结列表

    Returns:
        是否保存成功
    """
    conn = connect_db(db_url)
    data = json.dumps(summaries, ensure_ascii=False)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE transcripts 
                    SET summaries_json = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (data, transcript_id),
                )
                return cur.rowcount > 0
    finally:
        conn.close()


def get_summaries(
    db_url: Optional[str], transcript_id: int
) -> Optional[List[Dict[str, Any]]]:
    """获取已保存的总结。

    Args:
        db_url: 数据库连接 URL
        transcript_id: 转写记录 ID

    Returns:
        总结列表，如果不存在或为空返回 None
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT summaries_json FROM transcripts WHERE id = %s",
                    (int(transcript_id),),
                )
                row = cur.fetchone()
                if not row or not row.get("summaries_json"):
                    return None
                try:
                    return json.loads(row["summaries_json"])
                except Exception:
                    return None
    finally:
        conn.close()