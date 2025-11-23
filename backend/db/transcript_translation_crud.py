# -*- coding: utf-8 -*-
"""转写记录翻译 CRUD 操作模块"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from .conn_utils import connect_db


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