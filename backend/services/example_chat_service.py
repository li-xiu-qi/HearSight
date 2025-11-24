# -*- coding: utf-8 -*-
"""chat_service 示例测试"""

import sys
import os
import warnings

# 忽略 litellm 的异步客户端清理警告
warnings.filterwarnings("ignore", message="coroutine 'close_litellm_async_clients' was never awaited")

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.services.knowledge_base_service import knowledge_base
from backend.services.chat_service import chat_service

def test_chat_service():
    """测试 chat_service 的流式调用"""

    # 模拟参数
    question = "视频讲了什么？"


    print(f"问题: {question}")

    # 检查知识库中的 transcript_ids
    available_ids = knowledge_base.get_transcript_ids()
    print(f"知识库中的 transcript_ids: {available_ids}")

    # 使用所有可用的 transcript_ids 进行检索
    transcript_ids = available_ids

    # 收集流式响应
    full_response = []

    def stream_callback(chunk: str):
        print(chunk, end="", flush=True)
        full_response.append(chunk)

    try:
        # 调用 chat_service
        generator = chat_service.chat_with_transcripts_stream(
            question=question,
            transcript_ids=transcript_ids,
            stream_callback=stream_callback
        )

        # 消费生成器以触发执行，即使有 callback
        for _ in generator:
            pass

        print("=== 测试完成 ===")
        print(f"完整响应: {''.join(full_response)}")

    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_chat_service()
