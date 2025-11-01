# -*- coding: utf-8 -*-
"""转写记录表初始化模块"""
from __future__ import annotations

from typing import Optional

from .conn_utils import connect_db


def init_transcript_table(db_url: Optional[str] = None) -> None:
    """初始化转写记录表和索引。"""
    conn = connect_db(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS transcripts (
                        id SERIAL PRIMARY KEY,
                        media_path TEXT NOT NULL,
                        segments_json TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT (now())
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_transcripts_media_path
                    ON transcripts(media_path);
                    """
                )
    finally:
        conn.close()
