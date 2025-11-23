# -*- coding: utf-8 -*-
"""chat_service 示例测试"""

import sys
import os

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.services.chat_service import chat_service
from backend.config import settings

def test_chat_service():
    """测试 chat_service 的流式调用"""

    # 模拟参数
    question = "请总结这个视频的内容"

    transcript_id = 1  # 假设有这个ID，测试时不要删除第一个转录媒体文件稿子

    print("=== 测试 chat_service 流式调用 ===")
    print(f"问题: {question}")
    print(f"转录ID: {transcript_id}")

    # 收集流式响应
    full_response = []

    def stream_callback(chunk: str):
        print(chunk, end="", flush=True)
        full_response.append(chunk)

    try:
        # 调用 chat_service
        generator = chat_service.chat_with_segments_stream(
            question=question,
            transcript_id=transcript_id,
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
