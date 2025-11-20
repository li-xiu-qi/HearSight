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
                # 创建表时直接包含所有字段
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS transcripts (
                        id SERIAL PRIMARY KEY,
                        audio_path TEXT NOT NULL,
                        video_path TEXT,
                        media_type TEXT NOT NULL DEFAULT 'audio',
                        segments_json TEXT NOT NULL,
                        summaries_json TEXT,
                        translations_json TEXT,
                        chat_messages_json TEXT,
                        created_at TIMESTAMP NOT NULL DEFAULT (now()),
                        updated_at TIMESTAMP NOT NULL DEFAULT (now())
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_transcripts_audio_path
                    ON transcripts(audio_path);
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE IF EXISTS transcripts
                    ADD COLUMN IF NOT EXISTS video_path TEXT;
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_transcripts_updated_at
                    ON transcripts(updated_at DESC);
                    """
                )
    finally:
        conn.close()
