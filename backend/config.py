"""配置管理模块

使用 Pydantic BaseSettings 进行应用配置管理，支持环境变量覆盖。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置。

    支持从环境变量读取，优先级：环境变量 > .env 文件 > 默认值
    """

    # --- Postgres (数据库) ---
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_db: Optional[str] = None
    postgres_port: Optional[int] = None

    # --- 服务端 / 前端 端口 ---
    backend_port: Optional[int] = None
    frontend_port: Optional[int] = None

    # --- LLM 配置 ---
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_provider_base_url: Optional[str] = None
    llm_provider_api_key: Optional[str] = None
    llm_context_length: Optional[int] = None
    llm_tpm: Optional[int] = None
    llm_rpm: Optional[int] = None

    # --- Embedding 配置 ---
    embedding_provider: Optional[str] = None
    embedding_provider_base_url: Optional[str] = None
    embedding_provider_api_key: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_context_length: Optional[int] = None
    embedding_dim: Optional[int] = None
    embedding_tpm: Optional[int] = None
    embedding_rpm: Optional[int] = None

    # --- 其他：B站 Cookie 等 ---
    bilibili_sessdata: Optional[str] = None
    downloads_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app_datas", "download_videos")

    # --- ASRBackend 服务 ---
    asr_backend_url: str = "http://localhost:8003"

    # --- Celery 配置 ---
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_time_limit: int = 3600
    celery_task_soft_time_limit: int = 3300
    celery_worker_concurrency: int = 4
    celery_log_level: str = "info"

    model_config = ConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()


# --- Celery 应用配置 ---

from celery import Celery

def create_celery_app() -> Celery:
    """创建和配置Celery应用。

    使用Redis作为消息broker和结果backend。
    """
    app = Celery("backend.queues")

    # 基础配置
    app.conf.update(
        # 消息队列配置
        broker_url=settings.celery_broker_url,
        result_backend=settings.celery_result_backend,

        # 消息序列化
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],

        # 时区
        timezone="Asia/Shanghai",
        enable_utc=True,

        # 任务配置
        task_track_started=True,  # 追踪任务开始
        task_time_limit=settings.celery_task_time_limit,  # 硬超时（秒）
        task_soft_time_limit=settings.celery_task_soft_time_limit,  # 软超时（秒）

        # 任务结果存储
        result_expires=86400,  # 结果保存24小时

        # 队列配置
        task_default_queue="default",
        task_default_exchange="default",
        task_default_routing_key="default",
    )

    # 任务队列定义
    app.conf.task_queues = {
        "default": {
            "exchange": "default",
            "routing_key": "default",
        },
        "download": {
            "exchange": "download",
            "routing_key": "download",
        },
        "asr": {
            "exchange": "asr",
            "routing_key": "asr",
        },
    }

    # 任务路由配置
    app.conf.task_routes = {
        "backend.queues.tasks.process_job_task": {
            "queue": "default",
            "routing_key": "default",
        },
    }

    # 自动发现任务
    app.autodiscover_tasks(["backend.queues"])

    return app
