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

    # --- OpenAI / AI 相关 ---
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_chat_model: Optional[str] = None
    chat_max_windows: Optional[int] = None

    # --- 其他：B站 Cookie 等 ---
    bilibili_sessdata: Optional[str] = None
    downloads_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app_datas", "download_videos")

    # --- ASRBackend 服务 ---
    asr_backend_url: str = "http://localhost:8003"

    model_config = ConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()