from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import os

from pydantic import BaseModel

# 指向同级目录下的 .env
ENV_FILE: Path = Path(__file__).with_name(".env")

# 模块级缓存，避免重复读取磁盘，缓存为 pydantic 的 Config 实例或 None
_config_cache: "Config" | None = None


class Config(BaseModel):
    # --- MinIO (对象存储) ---
    MINIO_ROOT_USER: Optional[str] = None
    MINIO_ROOT_PASSWORD: Optional[str] = None
    MINIO_PORT: Optional[int] = None
    MINIO_CONSOLE_PORT: Optional[int] = None

    # --- Postgres (数据库) ---
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None

    # --- 服务端 / 前端 端口 ---
    BACKEND_PORT: Optional[int] = None
    FRONTEND_PORT: Optional[int] = None

    # --- OpenAI / AI 相关 ---
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_CHAT_MODEL: Optional[str] = None
    CHAT_MAX_WINDOWS: Optional[int] = None

    # --- 其他：B站 Cookie 等 ---
    BILIBILI_SESSDATA: Optional[str] = None


def _parse_env(path: Path) -> Dict[str, str]:
    """解析简单的 .env 文件（支持注释、export 前缀、带引号的值和环境变量展开）。

    返回键->字符串值的字典。
    """
    result: Dict[str, str] = {}
    if not path.exists():
        return result

    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            # 支持 `export KEY=VALUE` 形式
            if line.startswith("export "):
                line = line[len("export "):].lstrip()
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip()
            # 去掉成对的引号
            if (val.startswith('"') and val.endswith('"')) or (
                val.startswith("'") and val.endswith("'")
            ):
                val = val[1:-1]
            # 展开类似 $VAR 或 ${VAR}
            val = os.path.expandvars(val)
            result[key] = val
    return result


def load_config(path: str | Path = ENV_FILE) -> Dict[str, Any]:
    """从 .env 文件读取配置并以 dict 返回。

    另外会将不存在的键写入 os.environ，便于项目中以环境变量方式访问。
    """
    p = Path(path)
    data = _parse_env(p)
    # 将未存在于环境的键写入 os.environ
    for k, v in data.items():
        if k not in os.environ:
            os.environ[k] = v
    return data or {}


def get_config() -> Config:
    """获取全局配置（返回 pydantic 的 `Config` 实例，带简单缓存）。

    第一次调用会从 `ENV_FILE` 读取并缓存为 `Config`，后续调用直接返回缓存内容。
    """
    global _config_cache
    if _config_cache is None:
        raw = load_config(ENV_FILE)
        # 让 pydantic 尝试根据字段类型进行转换（例如将字符串转换为 int）
        _config_cache = Config(**raw)
    return _config_cache


def reload_config() -> Config:
    """强制重新加载配置并更新缓存，返回新的 `Config` 实例。"""
    global _config_cache
    raw = load_config(ENV_FILE)
    _config_cache = Config(**raw)
    return _config_cache

if __name__ == "__main__":
    config = get_config()
    print(config)