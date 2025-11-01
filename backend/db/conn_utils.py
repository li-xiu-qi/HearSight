# -*- coding: utf-8 -*-
"""数据库连接工具模块"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import psycopg2


def ensure_conn_params(db_url: Optional[str] = None) -> Dict[str, Any]:
    """从 db_url 或环境变量解析连接参数。

    db_url 可接受像 psycopg2.connect 的 dsn 或完整 URL，也可以为空（使用默认本地 postgres）。
    返回可传入 psycopg2.connect 的 dict。
    """
    if db_url:
        return {"dsn": db_url}

    params: Dict[str, Any] = {}
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    dbname = os.environ.get("POSTGRES_DB")
    params["host"] = host
    params["port"] = int(port) if port else 5432
    if user:
        params["user"] = user
    if password:
        params["password"] = password
    if dbname:
        params["dbname"] = dbname
    return params


def connect_db(db_url: Optional[str] = None, max_retries: int = 30, retry_delay: int = 2) -> psycopg2.extensions.connection:
    """建立数据库连接，支持重试机制。

    Args:
        db_url: 数据库连接 URL 或 DSN，为空则使用环境变量
        max_retries: 最大重试次数
        retry_delay: 重试延迟时间（秒）

    Returns:
        psycopg2 连接对象

    Raises:
        RuntimeError: 无法建立数据库连接
    """
    conn_params = ensure_conn_params(db_url)

    for attempt in range(max_retries):
        try:
            if "dsn" in conn_params:
                conn = psycopg2.connect(conn_params["dsn"])  # type: ignore[arg-type]
            else:
                conn = psycopg2.connect(**conn_params)
            return conn
        except psycopg2.OperationalError as e:
            if "the database system is starting up" in str(e) or "Connection refused" in str(e):
                if attempt < max_retries - 1:
                    print(f"数据库尚未就绪，等待 {retry_delay} 秒后重试... (第 {attempt + 1}/{max_retries} 次)")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"数据库连接失败，已重试 {max_retries} 次")
                    raise
            else:
                raise

    raise RuntimeError("无法建立数据库连接")
