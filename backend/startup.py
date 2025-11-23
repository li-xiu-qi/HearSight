# -*- coding: utf-8 -*-
"""应用启动初始化"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from backend.db.transcript_init import init_transcript_table
from backend.db.job_base_store import init_job_table
from backend.config import settings
from litellm import Router

# 全局 LLM Router
llm_router = None

# 全局 Embedding Router
embedding_router = None


def initialize_llm_router():
    """初始化全局 LLM Router"""
    global llm_router

    if llm_router is not None:
        return llm_router

    # 构建模型参数
    model = f"{settings.llm_provider}/{settings.llm_model}"
    api_key = settings.llm_provider_api_key
    base_url = settings.llm_provider_base_url
    tpm = settings.llm_tpm
    rpm = settings.llm_rpm

    # 配置模型列表
    model_list = [{
        "model_name": settings.llm_model,
        "litellm_params": {
            "model": model,
            "api_key": api_key,
            "base_url": base_url,
            "tpm": tpm,
            "rpm": rpm,
        }
    }]

    # 创建 Router
    llm_router = Router(model_list=model_list)
    return llm_router


def initialize_embedding_router():
    """初始化全局 Embedding Router"""
    global embedding_router

    if embedding_router is not None:
        return embedding_router

    # 配置模型列表
    model_list = [{
        "model_name": settings.embedding_model,
        "litellm_params": {
            "model": settings.embedding_model,
            "api_key": settings.embedding_provider_api_key,
            "api_base": settings.embedding_provider_base_url,
            "custom_llm_provider": settings.embedding_provider,
        },
        "tpm": settings.embedding_tpm,
        "rpm": settings.embedding_rpm,
    }]

    # 创建 Router
    embedding_router = Router(model_list=model_list)
    return embedding_router


def get_llm_router():
    """获取全局 LLM Router"""
    global llm_router
    if llm_router is None:
        return initialize_llm_router()
    return llm_router


def get_embedding_router():
    """获取全局 Embedding Router"""
    global embedding_router
    if embedding_router is None:
        return initialize_embedding_router()
    return embedding_router


def initialize_app() -> tuple[Path, str | None]:
    """初始化应用配置并返回静态目录和数据库URL。

    初始化步骤：
    1. 加载 .env 文件
    2. 创建视频下载目录
    3. 初始化数据库
    """
    # 加载 .env 文件中的环境变量
    env_file = Path(__file__).parent.resolve() / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    app_dir = Path(__file__).parent.parent.resolve()
    static_dir = (app_dir / "app_datas" / "download_videos").resolve()
    static_dir.mkdir(parents=True, exist_ok=True)

    db_url = os.environ.get("POSTGRES_DSN") or os.environ.get("DATABASE_URL") or f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    init_transcript_table(db_url)
    init_job_table(db_url)

    # 初始化 LLM Router
    initialize_llm_router()

    # 初始化 Embedding Router（移到懒初始化中）
    # initialize_embedding_router()

    return static_dir, db_url


def get_db_url() -> str:
    """获取数据库URL"""
    return os.environ.get("POSTGRES_DSN") or os.environ.get("DATABASE_URL") or f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"


def get_backend_port() -> int:
    """获取后端启动端口。从settings获取"""
    if settings.backend_port:
        return int(settings.backend_port)
    return 8000
