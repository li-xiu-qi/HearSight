# -*- coding: utf-8 -*-
"""转写记录聊天消息 CRUD 操作模块"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from .conn_utils import connect_db


def save_chat_messages(
    db_url: Optional[str], transcript_id: int, messages: List[Dict[str, Any]]
) -> bool:
    """保存chat消息到数据库。

    Args:
        db_url: 数据库连接 URL
        transcript_id: 转写记录 ID
        messages: chat消息列表

    Returns:
        是否保存成功
    """
    conn = connect_db(db_url)
    data = json.dumps(messages, ensure_ascii=False)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE transcripts 
                    SET chat_messages_json = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (data, transcript_id),
                )
                return cur.rowcount > 0
    finally:
        conn.close()


def get_chat_messages(
    db_url: Optional[str], transcript_id: int
) -> Optional[List[Dict[str, Any]]]:
    """获取已保存的chat消息。

    Args:
        db_url: 数据库连接 URL
        transcript_id: 转写记录 ID

    Returns:
        chat消息列表，如果不存在或为空返回 None
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT chat_messages_json FROM transcripts WHERE id = %s",
                    (int(transcript_id),),
                )
                row = cur.fetchone()
                if not row or not row.get("chat_messages_json"):
                    return None
                try:
                    return json.loads(row["chat_messages_json"])
                except Exception:
                    return None
    finally:
        conn.close()


def clear_chat_messages(db_url: Optional[str], transcript_id: int) -> bool:
    """清空chat消息。

    Args:
        db_url: 数据库连接 URL
        transcript_id: 转写记录 ID

    Returns:
        是否清空成功
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE transcripts 
                    SET chat_messages_json = NULL, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (transcript_id,),
                )
                return cur.rowcount > 0
    finally:
        conn.close()