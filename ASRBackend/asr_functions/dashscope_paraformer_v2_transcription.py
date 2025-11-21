"""DashScope Paraformer-v2 音频转录模块

使用阿里云 DashScope API 的 Paraformer-v2 模型进行异步音频转录，支持多语言识别。
"""

import os
import time
from http import HTTPStatus
from typing import Dict, List, Optional

import requests

try:
    import dashscope
    from dashscope.audio.asr import Transcription
except ImportError:
    dashscope = None
    Transcription = None

from .segment_normalizer import extract_text, normalize_segments
from .utils import detect_language

MODEL_NAME = "paraformer-v2"


def initialize_dashscope_client(api_key: str) -> None:
    """初始化 DashScope 客户端"""
    if dashscope is None:
        raise ImportError("dashscope 未安装")
    dashscope.api_key = api_key
    os.environ['DASHSCOPE_API_KEY'] = api_key
    print("DashScope 客户端初始化成功")


def async_transcribe_audio(
    file_urls: List[str],
    model: str = MODEL_NAME,
    language_hints: Optional[List[str]] = None,
) -> Optional[str]:
    """异步转录音频文件

    Returns:
        task_id: 任务 ID，失败返回 None
    """
    if Transcription is None:
        raise ImportError("dashscope 未安装")

    if language_hints is None:
        language_hints = ["zh", "en"]

    try:
        task_response = Transcription.async_call(
            model=model,
            file_urls=file_urls,
            language_hints=language_hints,
        )
        if task_response.status_code == HTTPStatus.OK:
            task_id = task_response.output.task_id
            print(f"任务提交成功，任务 ID: {task_id}")
            return task_id
        else:
            print(f"任务提交失败: {task_response}")
            return None
    except Exception as e:
        print(f"提交任务异常: {e}")
        return None


def get_transcription_status(task_id: str, wait_timeout: int = 0) -> Optional[Dict]:
    """获取转录任务状态"""
    if Transcription is None:
        raise ImportError("dashscope 未安装")

    try:
        status_response = Transcription.wait(task=task_id, timeout=wait_timeout)
        if status_response.status_code == HTTPStatus.OK:
            return status_response.output
        else:
            print(f"获取状态失败: {status_response}")
            return None
    except Exception as e:
        print(f"查询状态异常: {e}")
        return None


def _parse_transcription_result(result: Dict) -> Optional[List[Dict]]:
    """解析 DashScope 转录结果"""
    if not result or "transcripts" not in result:
        return None

    segments = []
    try:
        for transcript in result.get("transcripts", []):
            channel_id = transcript.get("channel_id", 0)
            spk_id = str(channel_id)

            for sentence in transcript.get("sentences", []):
                segment = {
                    "spk_id": spk_id,
                    "sentence": sentence.get("text", ""),
                    "start_time": float(sentence.get("begin_time", 0)),
                    "end_time": float(sentence.get("end_time", 0)),
                }
                segments.append(segment)

        segments.sort(key=lambda x: x["start_time"])
        return segments if segments else None
    except Exception as e:
        print(f"解析结果异常: {e}")
        return None


def transcribe_audio_from_url(
    url: str,
    model: str = MODEL_NAME,
    language_hints: Optional[List[str]] = None,
    timeout: int = 600,
) -> Optional[Dict]:
    """完整的工作流：从 URL 转录音频并返回标准化结果

    Args:
        url: 音频文件 URL
        model: 转录模型
        language_hints: 语言提示
        timeout: 等待超时时间（秒）

    Returns:
        标准化后的转录结果字典
    """
    if language_hints is None:
        language_hints = ["zh", "en"]

    print(f"开始转录: {url}")

    # 提交任务
    task_id = async_transcribe_audio([url], model, language_hints)
    if not task_id:
        return {"status": "error", "error": "提交转录任务失败"}

    # 等待完成
    start_time = time.time()
    max_attempts = 60  # 最大检查次数
    interval = 5  # 检查间隔

    for attempt in range(max_attempts):
        if time.time() - start_time > timeout:
            print("转录超时")
            return {"status": "error", "error": "转录超时"}

        print(f"检查状态 ({attempt + 1}/{max_attempts})")
        result = get_transcription_status(task_id, wait_timeout=5)

        if not result:
            time.sleep(interval)
            continue

        task_status = result.get("task_status")
        print(f"任务状态: {task_status}")

        if task_status == "SUCCEEDED":
            # 查找成功的子任务
            for item in result.get("results", []):
                if item.get("subtask_status") == "SUCCEEDED":
                    transcription_url = item.get("transcription_url")
                    if transcription_url:
                        print(f"转录完成，获取结果: {transcription_url}")
                        break
            else:
                transcription_url = None

            if not transcription_url:
                return {
                    "status": "error",
                    "error": "未找到转录结果 URL",
                    "task_status": task_status,
                }

            # 获取转录数据
            try:
                response = requests.get(transcription_url)
                if response.status_code != 200:
                    return {"status": "error", "error": f"获取结果失败: HTTP {response.status_code}"}

                transcription_data = response.json()
                segments = _parse_transcription_result(transcription_data)

                if not segments:
                    return {"status": "error", "error": "解析转录结果为空"}

                normalized_segments = normalize_segments(segments)
                text_content = extract_text(normalized_segments)
                language = detect_language(text_content)

                return {
                    "filename": os.path.basename(url),
                    "text": text_content,
                    "language": language,
                    "segments": normalized_segments,
                    "status": "success",
                    "task_id": task_id,
                }

            except Exception as e:
                return {"status": "error", "error": f"获取结果异常: {str(e)}"}

        elif task_status == "FAILED":
            return {
                "status": "error",
                "error": "转录任务失败",
                "task_status": task_status,
            }

        time.sleep(interval)

    return {"status": "error", "error": "等待超时"}
