"""ASR 后端配置管理模块

使用 Pydantic BaseSettings 进行应用配置管理，支持环境变量覆盖。
优先级：环境变量 > .env 文件 > 默认值

支持两种运行模式：
- local: 使用本地 FunASR 模型（需要 torch 和大量模型文件）
- cloud: 使用阿里云 DashScope API（轻量级，仅需网络连接）
"""

from __future__ import annotations

import os
from typing import List, Literal

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class ASRBackendSettings(BaseSettings):
    """ASR 后端配置类

    支持本地和云端两种运行模式，可通过环境变量 ASR_MODE 切换
    """

    app_name: str = "HearSight ASR Backend"
    debug: bool = True
    port: int = 8003

    cors_origins_str: str = (
        "http://localhost:5173,http://localhost:8080,http://localhost:8000"
    )
    cors_allow_credentials: bool = True
    cors_allow_methods_str: str = "*"
    cors_allow_headers_str: str = "*"

    # 运行模式：local（本地模型）或 cloud（云端 API）
    asr_mode: Literal["local", "cloud"] = "cloud"

    # ========== 本地模式配置 ==========
    # 仅在 asr_mode == "local" 时使用
    local_model_name: str = "paraformer-zh"
    local_model_revision: str = "v2.0.4"
    local_vad_model: str = "fsmn-vad"
    local_vad_model_revision: str = "v2.0.4"
    local_punc_model: str = "ct-punc-c"
    local_punc_model_revision: str = "v2.0.4"
    local_spk_model: str = "cam++"

    # ========== 云端模式配置 ==========
    # 仅在 asr_mode == "cloud" 时使用
    dashscope_api_key: str = ""
    dashscope_model: str = "paraformer-v2"
    dashscope_language_hints: str = "zh,en"

    # ========== Supabase 配置 ==========
    # 用于云端模式的文件上传存储
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_bucket_name: str = "test-public"
    supabase_folder_name: str = "asr"
    supabase_admin_email: str = ""
    supabase_admin_password: str = ""

    # 文件名映射记录文件路径
    filename_mapping_file: str = os.path.join(
        os.path.dirname(__file__), "cache", "filename_mapping.json"
    )

    model_config = ConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> List[str]:
        """CORS origins 列表"""
        return [
            origin.strip()
            for origin in self.cors_origins_str.split(",")
            if origin.strip()
        ]

    @property
    def cors_allow_methods(self) -> List[str]:
        """CORS 允许的方法"""
        if self.cors_allow_methods_str == "*":
            return ["*"]
        return [
            method.strip()
            for method in self.cors_allow_methods_str.split(",")
            if method.strip()
        ]

    @property
    def cors_allow_headers(self) -> List[str]:
        """CORS 允许的请求头"""
        if self.cors_allow_headers_str == "*":
            return ["*"]
        return [
            header.strip()
            for header in self.cors_allow_headers_str.split(",")
            if header.strip()
        ]

    def is_local_mode(self) -> bool:
        """检查是否为本地模式"""
        return self.asr_mode == "local"

    def is_cloud_mode(self) -> bool:
        """检查是否为云端模式"""
        return self.asr_mode == "cloud"

    def validate_config(self) -> None:
        """验证配置的有效性"""
        if self.is_cloud_mode() and not self.dashscope_api_key:
            raise ValueError(
                "云端模式需要设置 dashscope_api_key，"
                "请设置环境变量 DASHSCOPE_API_KEY 或在 .env 文件中配置"
            )


settings = ASRBackendSettings()
