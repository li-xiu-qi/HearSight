# -*- coding: utf-8 -*-
"""应用启动初始化"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from config import settings
from backend.db.pg_store import init_db


def initialize_app() -> tuple[Path, str | None]:
    """初始化应用配置并返回静态目录和数据库URL。

    初始化步骤：
    1. 加载 .env 文件
    2. 创建视频下载目录
    3. 初始化数据库
    """
    # 加载 .env 文件中的环境变量
    env_file = Path(__file__).parent.parent.resolve() / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    app_dir = Path(__file__).parent.parent.resolve()
    static_dir = (app_dir / "app_datas" / "download_videos").resolve()
    static_dir.mkdir(parents=True, exist_ok=True)

    db_url = os.environ.get("POSTGRES_DSN") or os.environ.get("DATABASE_URL")
    init_db(db_url)

    return static_dir, db_url


def get_backend_port() -> int:
    """获取后端启动端口。优先级：PORT 环境变量 > settings > 8000"""
    if env_port := os.environ.get("PORT"):
        return int(env_port)
    if settings.backend_port:
        return int(settings.backend_port)
    return 8000
