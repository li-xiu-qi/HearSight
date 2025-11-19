"""DashScope Paraformer-v2 转录功能使用示例

演示如何使用集成到 ASRBackend 中的 DashScope Paraformer-v2 转录功能。
"""

import asyncio
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ASRBackend.asr_functions.dashscope_paraformer_v2_transcription import (
    MODEL_NAME,
    _parse_transcription_result,
    async_transcribe_audio,
    get_transcription_status,
    initialize_dashscope_client,
    transcribe_audio_from_url,
)
from ASRBackend.config import settings


async def example_async_transcription():
    """示例：异步转录流程"""
    print("=== DashScope Paraformer-v2 异步转录示例 ===\n")
    print(f"使用模型: {MODEL_NAME}\n")

    # 初始化客户端
    initialize_dashscope_client(settings.dashscope_api_key)

    # 1. 提交转录任务
    file_urls = [
        "https://sbp-7fgelj2azms1xag5.supabase.opentrust.net/storage/v1/object/public/test-public/asr/test.mp4"
    ]

    print("1. 提交转录任务...")
    task_id = async_transcribe_audio(
        file_urls=file_urls,
        model=MODEL_NAME,
        language_hints=["zh", "en"],
    )

    if not task_id:
        print("❌ 提交失败")
        return

    print(f"✓ 任务已提交，Task ID: {task_id}\n")

    # 2. 定期查询任务状态
    print("2. 查询任务状态...")
    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        status = get_transcription_status(task_id)

        if status:
            task_status = status.get("task_status")
            print(f"   任务状态: {task_status}")

            if task_status == "SUCCEEDED":
                print("✓ 转录完成\n")
                result = status
                break
            elif task_status == "FAILED":
                print("❌ 转录失败")
                return
        else:
            print("   查询失败")

        retry_count += 1
        if retry_count < max_retries:
            await asyncio.sleep(2)

    else:
        print("⚠ 超过最大重试次数，停止等待")
        return

    # 3. 解析结果
    print("3. 解析转录结果...")
    parsed_segments = _parse_transcription_result(result)

    if parsed_segments:
        print(f"✓ 解析完成，共 {len(parsed_segments)} 条分段")

        # 显示转录结果
        print("\n4. 转录结果详情:")
        for segment in parsed_segments:
            print(
                f"   [{segment.get('index', 0)}] ({segment['spk_id']}) {segment['start_time']:.0f}ms - {segment['end_time']:.0f}ms"
            )
            print(f"       {segment['sentence']}")
    else:
        print("⚠ 解析结果为空")


async def example_wait_for_result():
    """示例：等待转录结果"""
    print("=== DashScope Paraformer-v2 等待结果示例 ===\n")
    print(f"使用模型: {MODEL_NAME}\n")

    # 初始化客户端
    initialize_dashscope_client(settings.dashscope_api_key)

    file_urls = [
        "https://sbp-7fgelj2azms1xag5.supabase.opentrust.net/storage/v1/object/public/test-public/asr/test.mp4"
    ]

    print("1. 提交转录任务...")
    task_id = async_transcribe_audio(
        file_urls=file_urls,
        model=MODEL_NAME,
        language_hints=["zh", "en"],
    )

    if not task_id:
        print("❌ 提交失败")
        return

    print(f"✓ 任务已提交，Task ID: {task_id}\n")

    print("2. 等待转录完成（最长 10 分钟）...")
    result = get_transcription_status(task_id, wait_timeout=600)

    if result:
        print("✓ 转录完成\n")
        print(f"任务状态: {result.get('task_status')}")
        print(f"结果数量: {len(result.get('results', []))}")
    else:
        print("❌ 等待结果失败或超时")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "wait":
        asyncio.run(example_wait_for_result())
    else:
        asyncio.run(example_async_transcription())
