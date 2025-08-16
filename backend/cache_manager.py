"""
基于 diskcache 的轻量缓存：用音频前 N 字节 + 模型名 计算哈希作为 key，缓存其转写文本。

用法建议：
- 在语音识别前：
    key = audio_key(audio_path, model_name)  # 默认读取前 8KB
    text = get_text(key)
    if text is not None:
        return text
- 识别完成后：
    set_text(key, recognized_text, model=model_name, meta={...})

说明：
- 缓存目录：backend/cache/，使用 diskcache.Cache 落盘；
- key 由：模型名 + 音频前缀字节 共同参与 SHA256 计算；
- 仅做最小实现，避免过度 try/except；异常直接抛出便于定位。
"""

from __future__ import annotations

import hashlib
import os
from typing import Optional, Dict, Any

from diskcache import Cache

# 缓存目录（与本文件同级的 cache/）
_CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")

# 默认读取的音频前缀字节数（8KB）
DEFAULT_PREFIX_BYTES = 8192


def _ensure_cache_dir() -> None:
    """确保缓存目录存在。"""
    if not os.path.isdir(_CACHE_DIR):
        os.makedirs(_CACHE_DIR, exist_ok=True)


def _cache() -> Cache:
    """返回全局缓存实例。"""
    _ensure_cache_dir()
    return Cache(_CACHE_DIR)


def audio_key(file_path: str, model: str, *, first_n_bytes: int = DEFAULT_PREFIX_BYTES) -> str:
    """读取音频前 first_n_bytes 字节，并结合模型名计算 SHA256，返回十六进制 key。"""
    with open(file_path, "rb") as f:
        chunk = f.read(first_n_bytes)
    h = hashlib.sha256()
    # 模型名纳入 key，支持不同模型的缓存并存
    h.update(model.encode("utf-8"))
    h.update(b"|")
    h.update(chunk)
    return h.hexdigest()


def _payload(text: str, *, model: Optional[str], meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """统一的缓存负载结构。"""
    data: Dict[str, Any] = {"text": text}
    if model is not None:
        data["model"] = model
    if meta:
        data["meta"] = meta
    return data


def get_entry(key: str) -> Optional[Dict[str, Any]]:
    """读取缓存条目（包含 text、model、meta 等），不存在返回 None。"""
    with _cache() as c:
        val = c.get(key, default=None)
    if val is None:
        return None
    if isinstance(val, dict):
        return val
    # 兼容极简存储为纯文本的情况
    return {"text": str(val)}


def get_text(key: str) -> Optional[str]:
    """读取缓存的文本内容，若不存在则返回 None。"""
    entry = get_entry(key)
    return None if entry is None else entry.get("text")


def set_text(
    key: str,
    text: str,
    *,
    model: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    expire: Optional[int] = None,
) -> str:
    """写入/覆盖缓存文本，返回 key（兼容原有调用者期待字符串返回）。

    - model: 可选，冗余记录模型名（虽然已参与 key 计算，便于排查）；
    - meta: 可选，附加信息；
    - expire: 可选，过期时间（秒）。
    """
    payload = _payload(text, model=model, meta=meta)
    with _cache() as c:
        c.set(key, payload, expire=expire)
    return key


__all__ = [
    "DEFAULT_PREFIX_BYTES",
    "audio_key",
    "get_text",
    "set_text",
    "get_entry",
]
