# -*- coding: utf-8 -*-
"""聊天会话 CRUD 操作模块"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from .conn_utils import connect_db


def create_chat_session(
    db_url: Optional[str], title: Optional[str] = None
) -> int:
    """创建新的chat会话。

    Args:
        db_url: 数据库连接 URL
        title: 会话标题（可选）

    Returns:
        新创建的会话ID
    """
    conn = connect_db(db_url)
    # 调试打印：db_url（注意：可能包含敏感信息）
    print(f"[DEBUG] create_chat_session db_url={db_url}")
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_sessions (title)
                    VALUES (%s)
                    RETURNING id
                    """,
                    (title,),
                )
                result = cur.fetchone()
                session_id = result[0] if result else 0
                # 调试打印：创建会话 id 与 title
                print(f"[DEBUG] create_chat_session: title={title!r}, session_id={session_id}")
                return session_id
    finally:
        conn.close()


def get_chat_sessions(
    db_url: Optional[str], limit: int = 50, offset: int = 0
) -> List[Dict[str, Any]]:
    """获取chat会话列表。

    Args:
        db_url: 数据库连接 URL
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        会话列表
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, title, created_at, updated_at
                    FROM chat_sessions
                    ORDER BY updated_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset),
                )
                return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_chat_session(
    db_url: Optional[str], session_id: int
) -> Optional[Dict[str, Any]]:
    """获取单个chat会话。

    Args:
        db_url: 数据库连接 URL
        session_id: 会话ID

    Returns:
        会话信息
    """
    conn = connect_db(db_url)
    print(f"[DEBUG] get_chat_session db_url={db_url}")
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, title, created_at, updated_at
                    FROM chat_sessions
                    WHERE id = %s
                    """,
                    (session_id,),
                )
                row = cur.fetchone()
                session = dict(row) if row else None
                # 调试打印：查询会话结果
                print(f"[DEBUG] get_chat_session: session_id={session_id}, session={session}")
                return session
    finally:
        conn.close()


def update_chat_session_title(
    db_url: Optional[str], session_id: int, title: str
) -> bool:
    """更新chat会话标题。

    Args:
        db_url: 数据库连接 URL
        session_id: 会话ID
        title: 新标题

    Returns:
        是否更新成功
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE chat_sessions
                    SET title = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (title, session_id),
                )
                return cur.rowcount > 0
    finally:
        conn.close()


def delete_chat_session(db_url: Optional[str], session_id: int) -> bool:
    """删除chat会话（级联删除消息）。

    Args:
        db_url: 数据库连接 URL
        session_id: 会话ID

    Returns:
        是否删除成功
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM chat_sessions WHERE id = %s",
                    (session_id,),
                )
                return cur.rowcount > 0
    finally:
        conn.close()