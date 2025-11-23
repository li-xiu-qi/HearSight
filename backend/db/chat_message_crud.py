# -*- coding: utf-8 -*-
"""聊天消息 CRUD 操作模块"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from .conn_utils import connect_db
from datetime import datetime, timezone


def save_chat_messages(
    db_url: Optional[str], session_id: int, messages: List[Dict[str, Any]]
) -> bool:
    """保存chat消息到数据库。

    Args:
        db_url: 数据库连接 URL
        session_id: 会话ID
        messages: chat消息列表

    Returns:
        是否保存成功
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                # 调试打印：保存消息开始，打印 session_id 与 messages 长度
                print(f"[DEBUG] save_chat_messages: session_id={session_id}, messages_count={len(messages) if messages else 0}")
                # 先删除该 session 的所有旧消息
                cur.execute(
                    "DELETE FROM chat_messages WHERE session_id = %s",
                    (session_id,),
                )
                
                # 插入新消息
                for message in messages:
                    # 兼容前端使用的字段名：'type' 或 'role'
                    msg_type = message.get('type') or message.get('role') or 'user'
                    # 规范 msg_type，数据库约束仅支持 'user' 或 'ai'
                    if msg_type not in ('user', 'ai'):
                        msg_type = 'user'
                    # 处理 timestamp：支持 int/float 表示（秒或毫秒），或 ISO 字符串（例如 2025-11-23T13:11:35.443Z）
                    raw_ts = message.get('timestamp')
                    ts_dt = None
                    epoch_ms = None
                    if raw_ts is None:
                        # 如果没有 timestamp，就使用当前时间
                        ts_dt = datetime.now(timezone.utc)
                        epoch_ms = int(ts_dt.timestamp() * 1000)
                    elif isinstance(raw_ts, (int, float)):
                        val = int(raw_ts)
                        # 如果是秒级时间戳（例如 1e9），转换为毫秒
                        if val < 1e10:
                            epoch_ms = val * 1000
                        else:
                            epoch_ms = val
                        seconds = epoch_ms / 1000.0
                        ts_dt = datetime.fromtimestamp(seconds, timezone.utc)
                    elif isinstance(raw_ts, str):
                        # ISO 格式，例如 '2025-11-23T13:11:35.443Z'，将 Z 替换为 +00:00 以兼容 fromisoformat
                        try:
                            iso = raw_ts.replace('Z', '+00:00')
                            dt = datetime.fromisoformat(iso)
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                            ts_dt = dt
                            epoch_ms = int(dt.timestamp() * 1000)
                        except Exception:
                            # 尝试将字符串作为数字处理
                            try:
                                val = int(float(raw_ts))
                                if val < 1e10:
                                    epoch_ms = val * 1000
                                else:
                                    epoch_ms = val
                            except Exception:
                                # 解析失败则使用当前时间
                                ts_dt = datetime.now(timezone.utc)
                                epoch_ms = int(ts_dt.timestamp() * 1000)

                    # 打印每条将要插入的消息简要信息（包括解析后的 timestamp 和 type）
                    print(f"[DEBUG] insert chat message: session_id={session_id}, type={msg_type}, content_preview={str(message.get('content'))[:50]}, timestamp_ms={epoch_ms}")
                    cur.execute(
                        """
                        INSERT INTO chat_messages (session_id, message_type, content, timestamp)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            session_id,
                            msg_type,
                            message.get("content"),
                            # 将 Python datetime 对象插入到 TIMESTAMPTZ 列
                            ts_dt,
                        ),
                    )
                
                # 更新 session 的 updated_at
                cur.execute(
                    "UPDATE chat_sessions SET updated_at = NOW() WHERE id = %s",
                    (session_id,),
                )
                return True
    except Exception as e:
        # 将异常打印出来以便诊断
        print(f"[ERROR] save_chat_messages exception: session_id={session_id}, error={e}")
        return False
    finally:
        conn.close()


def get_chat_messages(
    db_url: Optional[str], session_id: int
) -> Optional[List[Dict[str, Any]]]:
    """获取已保存的chat消息。

    Args:
        db_url: 数据库连接 URL
        session_id: 会话ID

    Returns:
        chat消息列表，如果不存在或为空返回 None
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT message_type as type, content, timestamp, id
                    FROM chat_messages 
                    WHERE session_id = %s 
                    ORDER BY timestamp ASC
                    """,
                    (int(session_id),),
                )
                rows = cur.fetchall()
                if not rows:
                    return None
                
                # 转换格式以保持与前端兼容
                messages = []
                for row in rows:
                    # row['timestamp'] may be a datetime object (timestamptz); convert to epoch ms
                    ts_val = row.get('timestamp')
                    if isinstance(ts_val, datetime):
                        ts_ms = int(ts_val.timestamp() * 1000)
                    else:
                        try:
                            ts_ms = int(ts_val)
                        except Exception:
                            ts_ms = None

                    messages.append({
                        "id": f"{row['type']}-{ts_ms}",
                        "type": row["type"],
                        "content": row["content"],
                        "timestamp": ts_ms,
                    })
                return messages
    finally:
        conn.close()


def clear_chat_messages(db_url: Optional[str], session_id: int) -> bool:
    """清空chat消息。

    Args:
        db_url: 数据库连接 URL
        session_id: 会话ID

    Returns:
        是否清空成功
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM chat_messages WHERE session_id = %s",
                    (session_id,),
                )
                # 更新session的updated_at
                cur.execute(
                    "UPDATE chat_sessions SET updated_at = NOW() WHERE id = %s",
                    (session_id,),
                )
                return True
    except Exception as e:
        print(f"[ERROR] clear_chat_messages exception: session_id={session_id}, error={e}")
        return False
    finally:
        conn.close()