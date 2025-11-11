# -*- coding: utf-8 -*-
"""FastAPI 应用工厂"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routers import (
    chat_router,
    download_router,
    job_router,
    progress_router,
    thumbnail_router,
    transcript_router,
    upload_router,
)


def create_app(static_dir: Path, db_url: str | None) -> FastAPI:
    """创建并配置 FastAPI 应用。

    Args:
        static_dir: 静态文件目录（视频存放位置）
        db_url: 数据库连接字符串
    """
    app = FastAPI(title="HearSight API")

    # 配置 CORS
    allow_origins_env = os.environ.get("ALLOW_ORIGINS")
    if allow_origins_env:
        allow_origins = [s.strip() for s in allow_origins_env.split(",") if s.strip()]
    else:
        frontend_host = os.environ.get("FRONTEND_HOST")
        frontend_port = os.environ.get("FRONTEND_PORT")
        allow_origins = (
            [f"http://{frontend_host}:{frontend_port}"]
            if frontend_host and frontend_port
            else ["*"]
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 挂载静态目录和设置应用状态
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.state.static_dir = static_dir
    app.state.db_url = db_url

    # 注册路由
    app.include_router(download_router)
    app.include_router(transcript_router)
    app.include_router(job_router)
    app.include_router(chat_router)
    app.include_router(thumbnail_router)
    app.include_router(progress_router)
    app.include_router(upload_router)

    return app
