"""DashScope ASR 服务示例测试

演示如何使用阿里云 DashScope API 进行音频转录的完整流程。
此示例使用单个文件实现从提交任务到获取结果的整个过程。

注意：需要先设置 DASHSCOPE_API_KEY 环境变量或在 .env 文件中配置。
"""

import os
import time
import logging
from typing import Dict, List, Optional

import requests

try:
    import dashscope
    from dashscope.audio.asr import Transcription
except ImportError:
    print("❌ dashscope 未安装")
    exit(1)

# 导入配置
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from ASRBackend.config import settings

# 配置日志
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

MODEL_NAME = "paraformer-v2"


def initialize_client():
    """初始化 DashScope 客户端"""
    if not settings.dashscope_api_key:
        raise ValueError("❌ DASHSCOPE_API_KEY 未设置")
    dashscope.api_key = settings.dashscope_api_key


def submit_task(file_urls: List[str]) -> Optional[str]:
    """提交转录任务"""
    try:
        response = Transcription.async_call(
            model=settings.dashscope_model,
            file_urls=file_urls,
            language_hints=settings.dashscope_language_hints.split(","),
        )
        print("任务已提交，任务响应：", response)
        return response.output.task_id if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"提交任务异常: {e}")
        return None


def wait_completion(task_id: str) -> Optional[str]:
    """等待任务完成"""
    for _ in range(60):
        result = Transcription.wait(task=task_id, timeout=5).output
        print("任务状态：",result)
        if result.get("task_status") == "SUCCEEDED":
            for item in result.get("results", []):
                if item.get("subtask_status") == "SUCCEEDED":
                    return item.get("transcription_url")
        time.sleep(2)
    return None


def get_result(url: str) -> Optional[Dict]:
    """获取转录结果"""
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None


def parse_result(result: Dict) -> List[Dict]:
    """解析结果"""
    segments = []
    for transcript in result.get("transcripts", []):
        spk_id = str(transcript.get("channel_id", 0))
        for sentence in transcript.get("sentences", []):
            segments.append({
                "spk_id": spk_id,
                "sentence": sentence.get("text", ""),
                "start_time": float(sentence.get("begin_time", 0)),
                "end_time": float(sentence.get("end_time", 0)),
            })
    segments.sort(key=lambda x: x["start_time"])
    return segments


def extract_text(segments: List[Dict]) -> str:
    """提取文本"""
    return " ".join(s["sentence"] for s in segments if s["sentence"])


def detect_lang(text: str) -> str:
    """检测语言"""
    return "zh" if any('\u4e00' <= c <= '\u9fff' for c in text) else "en"


def main():
    """主函数"""
    try:
        initialize_client()
    except ValueError as e:
        print(e)
        return

    # 示例 URL
    audio_url = "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav"

    print("开始转录...")

    # 提交任务
    task_id = submit_task([audio_url])
    if not task_id:
        print("任务提交失败")
        return

    # 等待完成
    result_url = wait_completion(task_id)
    if not result_url:
        print("转录失败")
        return

    # 获取结果
    data = get_result(result_url)
    if not data:
        print("获取结果失败")
        return

    # 解析
    segments = parse_result(data)
    text = extract_text(segments)
    lang = detect_lang(text)

    print(f"文本: {text}")
    print(f"语言: {lang}")
    print(f"分段数: {len(segments)}")


if __name__ == "__main__":
    main()
    
"""
开始转录...
任务已提交，任务响应： {"status_code": 200, "request_id": "21d3cd9c-4955-4ec8-b429-dfed0568ac8b", "code": "", "message": "", "output": {"task_id": "3ab89906-decf-4fe4-8315-3400e7c02b26", "task_status": "PENDING"}, "usage": null}
任务状态： {"task_id": "3ab89906-decf-4fe4-8315-3400e7c02b26", "task_status": "SUCCEEDED", "submit_time": "2025-11-17 13:59:21.593", "scheduled_time": "2025-11-17 13:59:21.623", "end_time": "2025-11-17 13:59:36.466", "results": [{"file_url": "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav", "transcription_url": "https://dashscope-result-bj.oss-cn-beijing.aliyuncs.com/prod/paraformer-v2/20251117/13%3A59/bc08714f-35d7-469e-9951-fef1a7017879-1.json?Expires=1763445576&OSSAccessKeyId=LTAI5tQZd8AEcZX6KZV4G8qL&Signature=LaFHQDAzkeGnGOeC1yWWcob81xQ%3D", "subtask_status": "SUCCEEDED"}], "task_metrics": {"TOTAL": 1, "SUCCEEDED": 1, "FAILED": 0}}
文本: The birch canoe slid on the smooth planks, glued the sheet to the dark blue background.  It is easy to tell the depth overwell.  These days, a chicken leg is a rare dish.  Rice is often served in round bowls.  The juice of lemons makes fine punch.  The box was thrown beside the park truck.  The hogs are fed chopcorn and garbage.  Four hours of steawork faced us.  A large size in stockings is hard to sell. 
语言: en
分段数: 9
"""