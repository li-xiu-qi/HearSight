# -*- coding: utf-8 -*-
"""
ASR 音频处理模块（ASRBackend 客户端版本）

通过 ASRBackend 服务进行语音识别，保持原有接口兼容性。
ASRBackend 已预处理分段和规范化逻辑，本模块直接使用其结果。

支持本地和云端两种模式的 ASRBackend，自动选择合适的接口。
"""

import os
from typing import Dict, List

import requests

from backend.config import settings


def _get_asr_mode() -> str:
    """检测 ASRBackend 的运行模式。

    Returns:
        'local' 或 'cloud'
    """
    asr_url = settings.asr_backend_url.rstrip("/")
    try:
        response = requests.get(f"{asr_url}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("mode", "local")
    except requests.RequestException:
        return "local"


def _transcribe_local_mode(audio_path: str, asr_url: str) -> List[Dict]:
    """本地模式下调用字节流接口。"""
    with open(audio_path, "rb") as f:
        files = {"file": (os.path.basename(audio_path), f, "audio/mpeg")}
        response = requests.post(
            f"{asr_url}/asr/transcribe/bytes",
            files=files,
            timeout=300,
        )
        response.raise_for_status()

    result = response.json()
    if result.get("status") != "success":
        error_msg = result.get("error", "未知错误")
        raise RuntimeError(f"ASR 识别失败: {error_msg}")

    return result.get("segments", [])


def _transcribe_cloud_mode(audio_path: str, asr_url: str) -> List[Dict]:
    """云端模式下调用上传接口。"""
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")
    
    filename = os.path.basename(audio_path)
    file_size = os.path.getsize(audio_path)
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"准备上传音频文件到ASRBackend: {filename} (大小: {file_size_mb:.2f} MB)")
    
    with open(audio_path, "rb") as f:
        files = {"file": (filename, f)}
        try:
            response = requests.post(
                f"{asr_url}/asr/transcribe/upload",
                files=files,
                timeout=600,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"ASRBackend 返回错误状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            raise

    result = response.json()
    if result.get("status") != "success":
        error_msg = result.get("error", "未知错误")
        raise RuntimeError(f"ASR 识别失败: {error_msg}")

    return result.get("segments", [])


def process(
    audio_path: str
) -> List[Dict]:
    """
    处理音频并返回标准化列表，通过 ASRBackend 服务进行识别。

    ASRBackend 返回的结果已经是标准格式：
    [
        {
            "index": 1,
            "spk_id": "说话人ID",
            "sentence": "分段文本",
            "start_time": 起始时间毫秒,
            "end_time": 结束时间毫秒
        }
    ]

    Args:
        audio_path: 本地音频文件路径
        merge_sentences: 是否合并句子（由 ASRBackend 处理）
        merge_short_sentences: 是否合并短句子（由 ASRBackend 处理）

    Returns:
        标准化的分段列表，格式与原有接口兼容

    Raises:
        FileNotFoundError: 音频文件不存在
        requests.RequestException: ASRBackend 服务调用失败
        RuntimeError: ASR 识别失败
    """
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    asr_url = settings.asr_backend_url.rstrip("/")

    try:
        mode = _get_asr_mode()
        if mode == "local":
            segments = _transcribe_local_mode(audio_path, asr_url)
        else:
            segments = _transcribe_cloud_mode(audio_path, asr_url)

        os.makedirs("results", exist_ok=True)
        return segments

    except FileNotFoundError as e:
        raise FileNotFoundError(f"音频文件不存在: {audio_path}") from e
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"无法连接到 ASRBackend 服务（{asr_url}），请确保服务已启动"
        ) from e
    except requests.exceptions.Timeout as e:
        raise RuntimeError(f"ASRBackend 服务请求超时") from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"ASRBackend 服务调用失败: {str(e)}") from e
