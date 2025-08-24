# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


def init_db(db_path: str | Path) -> None:
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(p) as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_path TEXT NOT NULL,
                segments_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                started_at TEXT,
                finished_at TEXT,
                result_json TEXT,
                error TEXT
            );
            """
        )
        c.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_jobs_status_created
            ON jobs(status, created_at DESC);
            """
        )
        c.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_transcripts_media_path
            ON transcripts(media_path);
            """
        )
        conn.commit()


def save_transcript(db_path: str | Path, media_path: str, segments: List[Dict[str, Any]]) -> int:
    p = Path(db_path)
    data = json.dumps(segments, ensure_ascii=False)
    with sqlite3.connect(p) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO transcripts (media_path, segments_json) VALUES (?, ?)",
            (media_path, data),
        )
        conn.commit()
        return int(c.lastrowid)


def get_latest_transcript(db_path: str | Path, media_path: str) -> Optional[List[Dict[str, Any]]]:
    p = Path(db_path)
    if not p.exists():
        return None
    with sqlite3.connect(p) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT segments_json FROM transcripts
            WHERE media_path = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (media_path,),
        )
        row = c.fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return None


def list_transcripts_meta(db_path: str | Path, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """列出转写记录的元信息（不包含大字段），按id倒序。
    返回: [{id, media_path, created_at, segment_count}]
    """
    p = Path(db_path)
    if not p.exists():
        return []
    with sqlite3.connect(p) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT id, media_path, segments_json, created_at
            FROM transcripts
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (int(limit), int(offset)),
        )
        rows = c.fetchall()
        items: List[Dict[str, Any]] = []
        for rid, media_path, seg_json, created_at in rows:
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


def count_transcripts(db_path: str | Path) -> int:
    p = Path(db_path)
    if not p.exists():
        return 0
    with sqlite3.connect(p) as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM transcripts")
        row = c.fetchone()
        return int(row[0]) if row and row[0] is not None else 0


def get_transcript_by_id(db_path: str | Path, transcript_id: int) -> Optional[Dict[str, Any]]:
    p = Path(db_path)
    if not p.exists():
        return None
    with sqlite3.connect(p) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT id, media_path, segments_json, created_at
            FROM transcripts
            WHERE id = ?
            LIMIT 1
            """,
            (int(transcript_id),),
        )
        row = c.fetchone()
        if not row:
            return None
        rid, media_path, seg_json, created_at = row
        try:
            segs = json.loads(seg_json)
        except Exception:
            segs = []
        return {
            "id": int(rid),
            "media_path": str(media_path),
            "created_at": str(created_at),
            "segments": segs,
        }


# ------ jobs minimal queue ------

def create_job(db_path: str | Path, url: str) -> int:
    p = Path(db_path)
    with sqlite3.connect(p) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO jobs (url, status) VALUES (?, 'pending')",
            (url,),
        )
        conn.commit()
        return int(c.lastrowid)


def get_job(db_path: str | Path, job_id: int) -> Optional[Dict[str, Any]]:
    p = Path(db_path)
    if not p.exists():
        return None
    with sqlite3.connect(p) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, url, status, created_at, started_at, finished_at, result_json, error FROM jobs WHERE id = ?",
            (int(job_id),),
        )
        row = c.fetchone()
        if not row:
            return None
        rid, url, status, created_at, started_at, finished_at, result_json, error = row
        try:
            result = json.loads(result_json) if result_json else None
        except Exception:
            result = None
        return {
            "id": int(rid),
            "url": str(url),
            "status": str(status),
            "created_at": str(created_at) if created_at else None,
            "started_at": str(started_at) if started_at else None,
            "finished_at": str(finished_at) if finished_at else None,
            "result": result,
            "error": str(error) if error else None,
        }


def list_jobs(db_path: str | Path, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    p = Path(db_path)
    if not p.exists():
        return []
    with sqlite3.connect(p) as conn:
        c = conn.cursor()
        if status:
            c.execute(
                "SELECT id, url, status, created_at, started_at, finished_at, result_json, error FROM jobs WHERE status = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                (status, int(limit), int(offset)),
            )
        else:
            c.execute(
                "SELECT id, url, status, created_at, started_at, finished_at, result_json, error FROM jobs ORDER BY id DESC LIMIT ? OFFSET ?",
                (int(limit), int(offset)),
            )
        rows = c.fetchall()
        items: List[Dict[str, Any]] = []
        for rid, url, status, created_at, started_at, finished_at, result_json, error in rows:
            try:
                result = json.loads(result_json) if result_json else None
            except Exception:
                result = None
            items.append({
                "id": int(rid),
                "url": str(url),
                "status": str(status),
                "created_at": str(created_at) if created_at else None,
                "started_at": str(started_at) if started_at else None,
                "finished_at": str(finished_at) if finished_at else None,
                "result": result,
                "error": str(error) if error else None,
            })
        return items


def claim_next_pending_job(db_path: str | Path) -> Optional[Dict[str, Any]]:
    """原子领取一条 pending 任务并置为 running，返回任务信息。"""
    p = Path(db_path)
    with sqlite3.connect(p, isolation_level=None) as conn:  # autocommit off for BEGIN IMMEDIATE
        c = conn.cursor()
        # 锁表，防止并发领取
        c.execute("BEGIN IMMEDIATE")
        # 优先领取 pending
        c.execute(
            "SELECT id, url FROM jobs WHERE status = 'pending' ORDER BY id ASC LIMIT 1"
        )
        row = c.fetchone()
        if row:
            rid, url = row
            c.execute(
                "UPDATE jobs SET status = 'running', started_at = datetime('now') WHERE id = ?",
                (int(rid),),
            )
            c.execute("COMMIT")
            return {"id": int(rid), "url": str(url)}

        # 没有 pending，则尝试领取未完成的 running（finished_at 为空）以实现重启恢复
        c.execute(
            "SELECT id, url FROM jobs WHERE status = 'running' AND finished_at IS NULL ORDER BY started_at ASC LIMIT 1"
        )
        row2 = c.fetchone()
        if not row2:
            c.execute("COMMIT")
            return None
        rid2, url2 = row2
        # running 任务无需再次更新状态，直接返回
        c.execute("COMMIT")
        return {"id": int(rid2), "url": str(url2)}


def finish_job_success(db_path: str | Path, job_id: int, result: Dict[str, Any]) -> None:
    p = Path(db_path)
    with sqlite3.connect(p) as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE jobs SET status = 'success', finished_at = datetime('now'), result_json = ? WHERE id = ?",
            (json.dumps(result, ensure_ascii=False), int(job_id)),
        )
        conn.commit()


def finish_job_failed(db_path: str | Path, job_id: int, error: str) -> None:
    p = Path(db_path)
    with sqlite3.connect(p) as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE jobs SET status = 'failed', finished_at = datetime('now'), error = ? WHERE id = ?",
            (error, int(job_id)),
        )
        conn.commit()


def update_job_result(db_path: str | Path, job_id: int, patch: Dict[str, Any], status: Optional[str] = None) -> None:
    """合并写入 jobs.result_json，可选同时更新 status。
    - 若现有 result_json 不存在或非 JSON，则以 patch 作为新值。
    - status 若提供，则一并更新。
    """
    p = Path(db_path)
    with sqlite3.connect(p) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT result_json FROM jobs WHERE id = ?",
            (int(job_id),),
        )
        row = c.fetchone()
        current: Dict[str, Any]
        if row and row[0]:
            try:
                current = json.loads(row[0])
                if not isinstance(current, dict):
                    current = {}
            except Exception:
                current = {}
        else:
            current = {}

        current.update(patch or {})
        if status:
            c.execute(
                "UPDATE jobs SET result_json = ?, status = ? WHERE id = ?",
                (json.dumps(current, ensure_ascii=False), status, int(job_id)),
            )
        else:
            c.execute(
                "UPDATE jobs SET result_json = ? WHERE id = ?",
                (json.dumps(current, ensure_ascii=False), int(job_id)),
            )
        conn.commit()
