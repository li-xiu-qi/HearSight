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
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id SERIAL PRIMARY KEY,
                        title TEXT,
                        created_at TIMESTAMP NOT NULL DEFAULT (now()),
                        updated_at TIMESTAMP NOT NULL DEFAULT (now())
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id SERIAL PRIMARY KEY,
                        session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
                        message_type TEXT NOT NULL CHECK (message_type IN ('user', 'ai')),
                        content TEXT NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT (now())
                    );
                    """
                )

                # 如果旧表中 timestamp 仍是 BIGINT（epoch ms），尝试转换到 TIMESTAMPTZ
                try:
                    cur.execute(
                        "SELECT data_type FROM information_schema.columns WHERE table_name='chat_messages' AND column_name='timestamp'"
                    )
                    row = cur.fetchone()
                    if row and row[0] == 'bigint':
                        # 将 BIGINT 毫秒时间戳转换为 timestamptz
                        try:
                            cur.execute(
                                "ALTER TABLE chat_messages ALTER COLUMN timestamp TYPE TIMESTAMPTZ USING to_timestamp(timestamp::double precision / 1000.0);"
                            )
                            print('[DEBUG] Migrated chat_messages.timestamp from BIGINT to TIMESTAMPTZ')
                        except Exception as e:
                            print('[ERROR] Failed to migrate chat_messages.timestamp:', e)
                except Exception:
                    # 信息模式查询失败则忽略
                    pass
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at
                    ON chat_sessions(updated_at DESC);
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id
                    ON chat_messages(session_id);
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at
                    ON chat_messages(created_at DESC);
                    """
                )
    finally:
        conn.close()
