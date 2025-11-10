# -*- coding: utf-8 -*-
"""转写记录 CRUD 操作模块"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from .conn_utils import connect_db


def save_transcript(
    db_url: Optional[str],
    media_path: str,
    segments: List[Dict[str, Any]],
    media_type: str = "video",
) -> int:
    """保存转写记录。

    Args:
        db_url: 数据库连接 URL
        media_path: 媒体文件路径
        segments: 转写片段列表
        media_type: 媒体类型（'video' 或 'audio'）

    Returns:
        新创建的转写记录 ID
    """
    conn = connect_db(db_url)
    data = json.dumps(segments, ensure_ascii=False)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO transcripts (media_path, media_type, segments_json) VALUES (%s, %s, %s) RETURNING id",
                    (media_path, media_type, data),
                )
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("Failed to insert transcript")
                return int(row[0])
    finally:
        conn.close()


def update_transcript(
    db_url: Optional[str], transcript_id: int, segments: List[Dict[str, Any]]
) -> bool:
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


def get_transcript_by_id(
    db_url: Optional[str], transcript_id: int
) -> Optional[Dict[str, Any]]:
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
                    "media_type": str(row.get("media_type", "video")),
                    "created_at": str(row["created_at"]),
                    "segments": segs,
                }
    finally:
        conn.close()


def update_transcript_media_path(
    db_url: Optional[str], old_media_path: str, new_media_path: str
) -> int:
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


def save_translations(
    db_url: Optional[str],
    transcript_id: int,
    translations: Dict[str, List[Dict[str, Any]]],
) -> bool:
    """保存翻译结果到数据库。

    Args:
        db_url: 数据库连接 URL
        transcript_id: 转写记录 ID
        translations: 翻译结果字典（键为语言代码）

    Returns:
        是否保存成功
    """
    conn = connect_db(db_url)
    data = json.dumps(translations, ensure_ascii=False)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE transcripts 
                    SET translations_json = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (data, transcript_id),
                )
                return cur.rowcount > 0
    finally:
        conn.close()


def get_translations(
    db_url: Optional[str], transcript_id: int
) -> Optional[Dict[str, List[Dict[str, Any]]]]:
    """获取已保存的翻译。

    Args:
        db_url: 数据库连接 URL
        transcript_id: 转写记录 ID

    Returns:
        翻译字典，如果不存在或为空返回 None
    """
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT translations_json FROM transcripts WHERE id = %s",
                    (int(transcript_id),),
                )
                row = cur.fetchone()
                if not row or not row.get("translations_json"):
                    return None
                try:
                    return json.loads(row["translations_json"])
                except Exception:
                    return None
    finally:
        conn.close()


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
