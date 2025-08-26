# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor


def _ensure_conn_params(db_url: Optional[str] = None) -> Dict[str, Any]:
    """从 db_url 或环境变量解析连接参数。

    db_url 可接受像 psycopg2.connect 的 dsn 或完整 URL，也可以为空（使用默认本地 postgres）。
    返回可传入 psycopg2.connect 的 dict。
    """
    if db_url:
        return {"dsn": db_url}
    # 默认连接到本地 postgres，数据库名/用户/密码按常见环境变量设置
    import os

    params: Dict[str, Any] = {}
    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT")
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    dbname = os.environ.get("POSTGRES_DB")
    if host:
        params["host"] = host
    if port:
        params["port"] = port
    if user:
        params["user"] = user
    if password:
        params["password"] = password
    if dbname:
        params["dbname"] = dbname
    return params


def init_db(db_url: Optional[str] = None) -> None:
    """初始化 Postgres 中需要的表和索引。"""
    conn_params = _ensure_conn_params(db_url)
    # 当使用 dsn 键时，psycopg2.connect 接受 dsn 关键字参数
    if "dsn" in conn_params:
        conn = psycopg2.connect(conn_params["dsn"])  # type: ignore[arg-type]
    else:
        conn = psycopg2.connect(**conn_params)

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
                    CREATE TABLE IF NOT EXISTS jobs (
                        id SERIAL PRIMARY KEY,
                        url TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        created_at TIMESTAMP NOT NULL DEFAULT (now()),
                        started_at TIMESTAMP,
                        finished_at TIMESTAMP,
                        result_json TEXT,
                        error TEXT
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_jobs_status_created
                    ON jobs(status, created_at DESC);
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


def save_transcript(db_url: Optional[str], media_path: str, segments: List[Dict[str, Any]]) -> int:
    conn_params = _ensure_conn_params(db_url)
    data = json.dumps(segments, ensure_ascii=False)
    if "dsn" in conn_params:
        conn = psycopg2.connect(conn_params["dsn"])  # type: ignore[arg-type]
    else:
        conn = psycopg2.connect(**conn_params)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO transcripts (media_path, segments_json) VALUES (%s, %s) RETURNING id",
                    (media_path, data),
                )
                rid = cur.fetchone()[0]
                return int(rid)
    finally:
        conn.close()


def get_latest_transcript(db_url: Optional[str], media_path: str) -> Optional[List[Dict[str, Any]]]:
    conn_params = _ensure_conn_params(db_url)
    if "dsn" in conn_params:
        conn = psycopg2.connect(conn_params["dsn"])  # type: ignore[arg-type]
    else:
        conn = psycopg2.connect(**conn_params)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT segments_json FROM transcripts
                    WHERE media_path = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (media_path,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                try:
                    return json.loads(row[0])
                except Exception:
                    return None
    finally:
        conn.close()


def list_transcripts_meta(db_url: Optional[str], limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """列出转写记录的元信息（不包含大字段），按id倒序。
    返回: [{id, media_path, created_at, segment_count}]
    """
    conn_params = _ensure_conn_params(db_url)
    if "dsn" in conn_params:
        conn = psycopg2.connect(conn_params["dsn"])  # type: ignore[arg-type]
    else:
        conn = psycopg2.connect(**conn_params)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, media_path, segments_json, created_at
                    FROM transcripts
                    ORDER BY id DESC
                    LIMIT %s OFFSET %s
                    """,
                    (int(limit), int(offset)),
                )
                rows = cur.fetchall()
                items: List[Dict[str, Any]] = []
                for r in rows:
                    rid = r["id"]
                    media_path = r["media_path"]
                    seg_json = r["segments_json"]
                    created_at = r["created_at"]
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
    finally:
        conn.close()


def count_transcripts(db_url: Optional[str]) -> int:
    conn_params = _ensure_conn_params(db_url)
    if "dsn" in conn_params:
        conn = psycopg2.connect(conn_params["dsn"])  # type: ignore[arg-type]
    else:
        conn = psycopg2.connect(**conn_params)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM transcripts")
                row = cur.fetchone()
                return int(row[0]) if row and row[0] is not None else 0
    finally:
        conn.close()


def get_transcript_by_id(db_url: Optional[str], transcript_id: int) -> Optional[Dict[str, Any]]:
    conn_params = _ensure_conn_params(db_url)
    if "dsn" in conn_params:
        conn = psycopg2.connect(conn_params["dsn"])  # type: ignore[arg-type]
    else:
        conn = psycopg2.connect(**conn_params)
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
                    "created_at": str(row["created_at"]),
                    "segments": segs,
                }
    finally:
        conn.close()


# ------ jobs minimal queue ------

def create_job(db_url: Optional[str], url: str) -> int:
    conn_params = _ensure_conn_params(db_url)
    if "dsn" in conn_params:
        conn = psycopg2.connect(conn_params["dsn"])  # type: ignore[arg-type]
    else:
        conn = psycopg2.connect(**conn_params)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO jobs (url, status) VALUES (%s, %s) RETURNING id",
                    (url, 'pending'),
                )
                rid = cur.fetchone()[0]
                return int(rid)
    finally:
        conn.close()


def get_job(db_url: Optional[str], job_id: int) -> Optional[Dict[str, Any]]:
    conn_params = _ensure_conn_params(db_url)
    if "dsn" in conn_params:
        conn = psycopg2.connect(conn_params["dsn"])  # type: ignore[arg-type]
    else:
        conn = psycopg2.connect(**conn_params)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, url, status, created_at, started_at, finished_at, result_json, error FROM jobs WHERE id = %s",
                    (int(job_id),),
                )
                row = cur.fetchone()
                if not row:
                    return None
                try:
                    result = json.loads(row["result_json"]) if row["result_json"] else None
                except Exception:
                    result = None
                return {
                    "id": int(row["id"]),
                    "url": str(row["url"]),
                    "status": str(row["status"]),
                    "created_at": str(row["created_at"]) if row["created_at"] else None,
                    "started_at": str(row["started_at"]) if row["started_at"] else None,
                    "finished_at": str(row["finished_at"]) if row["finished_at"] else None,
                    "result": result,
                    "error": str(row["error"]) if row["error"] else None,
                }
    finally:
        conn.close()


def list_jobs(db_url: Optional[str], status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    conn_params = _ensure_conn_params(db_url)
    if "dsn" in conn_params:
        conn = psycopg2.connect(conn_params["dsn"])  # type: ignore[arg-type]
    else:
        conn = psycopg2.connect(**conn_params)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if status:
                    cur.execute(
                        "SELECT id, url, status, created_at, started_at, finished_at, result_json, error FROM jobs WHERE status = %s ORDER BY id DESC LIMIT %s OFFSET %s",
                        (status, int(limit), int(offset)),
                    )
                else:
                    cur.execute(
                        "SELECT id, url, status, created_at, started_at, finished_at, result_json, error FROM jobs ORDER BY id DESC LIMIT %s OFFSET %s",
                        (int(limit), int(offset)),
                    )
                rows = cur.fetchall()
                items: List[Dict[str, Any]] = []
                for r in rows:
                    try:
                        result = json.loads(r["result_json"]) if r["result_json"] else None
                    except Exception:
                        result = None
                    items.append({
                        "id": int(r["id"]),
                        "url": str(r["url"]),
                        "status": str(r["status"]),
                        "created_at": str(r["created_at"]) if r["created_at"] else None,
                        "started_at": str(r["started_at"]) if r["started_at"] else None,
                        "finished_at": str(r["finished_at"]) if r["finished_at"] else None,
                        "result": result,
                        "error": str(r["error"]) if r["error"] else None,
                    })
                return items
    finally:
        conn.close()


def claim_next_pending_job(db_url: Optional[str]) -> Optional[Dict[str, Any]]:
    """原子领取一条 pending 任务并置为 running，返回任务信息。"""
    conn_params = _ensure_conn_params(db_url)
    if "dsn" in conn_params:
        conn = psycopg2.connect(conn_params["dsn"])  # type: ignore[arg-type]
    else:
        conn = psycopg2.connect(**conn_params)
    try:
        # 使用事务与 SELECT ... FOR UPDATE SKIP LOCKED 来安全并发领取
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, url FROM jobs
                    WHERE status = 'pending'
                    ORDER BY id ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                    """
                )
                row = cur.fetchone()
                if row:
                    rid = int(row["id"])
                    url = row["url"]
                    cur.execute(
                        "UPDATE jobs SET status = 'running', started_at = now() WHERE id = %s",
                        (rid,),
                    )
                    return {"id": rid, "url": str(url)}

                # 没有 pending，则尝试领取未完成的 running（finished_at 为空）以实现重启恢复
                cur.execute(
                    """
                    SELECT id, url FROM jobs
                    WHERE status = 'running' AND finished_at IS NULL
                    ORDER BY started_at ASC
                    LIMIT 1
                    """
                )
                row2 = cur.fetchone()
                if not row2:
                    return None
                rid2 = int(row2["id"])
                url2 = row2["url"]
                return {"id": rid2, "url": str(url2)}
    finally:
        conn.close()


def finish_job_success(db_url: Optional[str], job_id: int, result: Dict[str, Any]) -> None:
    conn_params = _ensure_conn_params(db_url)
    if "dsn" in conn_params:
        conn = psycopg2.connect(conn_params["dsn"])  # type: ignore[arg-type]
    else:
        conn = psycopg2.connect(**conn_params)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE jobs SET status = 'success', finished_at = now(), result_json = %s WHERE id = %s",
                    (json.dumps(result, ensure_ascii=False), int(job_id)),
                )
    finally:
        conn.close()


def finish_job_failed(db_url: Optional[str], job_id: int, error: str) -> None:
    conn_params = _ensure_conn_params(db_url)
    if "dsn" in conn_params:
        conn = psycopg2.connect(conn_params["dsn"])  # type: ignore[arg-type]
    else:
        conn = psycopg2.connect(**conn_params)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE jobs SET status = 'failed', finished_at = now(), error = %s WHERE id = %s",
                    (error, int(job_id)),
                )
    finally:
        conn.close()


def update_job_result(db_url: Optional[str], job_id: int, patch: Dict[str, Any], status: Optional[str] = None) -> None:
    """合并写入 jobs.result_json，可选同时更新 status。
    - 若现有 result_json 不存在或非 JSON，则以 patch 作为新值。
    - status 若提供，则一并更新。
    """
    conn_params = _ensure_conn_params(db_url)
    if "dsn" in conn_params:
        conn = psycopg2.connect(conn_params["dsn"])  # type: ignore[arg-type]
    else:
        conn = psycopg2.connect(**conn_params)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT result_json FROM jobs WHERE id = %s",
                    (int(job_id),),
                )
                row = cur.fetchone()
                current: Dict[str, Any]
                if row and row.get("result_json"):
                    try:
                        current = json.loads(row.get("result_json"))
                        if not isinstance(current, dict):
                            current = {}
                    except Exception:
                        current = {}
                else:
                    current = {}

                current.update(patch or {})
                if status:
                    cur.execute(
                        "UPDATE jobs SET result_json = %s, status = %s WHERE id = %s",
                        (json.dumps(current, ensure_ascii=False), status, int(job_id)),
                    )
                else:
                    cur.execute(
                        "UPDATE jobs SET result_json = %s WHERE id = %s",
                        (json.dumps(current, ensure_ascii=False), int(job_id)),
                    )
    finally:
        conn.close()
