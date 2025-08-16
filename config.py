from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

# 指向同级目录下的 config.yaml
CONFIG_FILE: Path = Path(__file__).with_name("config.yaml")

# 模块级缓存，避免重复读取磁盘
_config_cache: Dict[str, Any] | None = None


def load_config(path: str | Path = CONFIG_FILE) -> Dict[str, Any]:
    """
    读取指定 YAML 配置文件并以 dict 返回。
    不做 try/except，出错让其抛出，便于定位问题。
    """
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def get_config() -> Dict[str, Any]:
    """
    获取全局配置（带简单缓存）。
    第一次调用会从 CONFIG_FILE 读取并缓存。
    后续调用直接返回缓存内容。
    """
    global _config_cache
    if _config_cache is None:
        _config_cache = load_config(CONFIG_FILE)
    return _config_cache


def reload_config() -> Dict[str, Any]:
    """强制重新加载配置并更新缓存。"""
    global _config_cache
    _config_cache = load_config(CONFIG_FILE)
    return _config_cache


__all__ = [
    "CONFIG_FILE",
    "load_config",
    "get_config",
    "reload_config",
]
