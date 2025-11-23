"""测试litellm的使用效果"""

import asyncio
import sys
import os

# 添加backend目录到路径
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from backend.startup import get_llm_router
from backend.config import settings

async def test_litellm_completion():
    """测试litellm的completion方法（非流式）"""
    llm_router = get_llm_router()

    messages = [
        {"role": "system", "content": "你是一个AI助手"},
        {"role": "user", "content": "什么是人工智能？"}
    ]

    try:
        response = llm_router.completion(
            model=settings.llm_model,
            messages=messages,
            temperature=0.3,
            max_tokens=200,
        )
        print("非流式调用成功")
        print("响应:", response.choices[0].message.content)
    except Exception as e:
        print("非流式调用失败:", str(e))

async def test_litellm_streaming():
    """测试litellm的completion方法（流式）"""
    llm_router = get_llm_router()

    messages = [
        {"role": "system", "content": "你是一个AI助手"},
        {"role": "user", "content": "简单介绍一下机器学习"}
    ]

    try:
        response = llm_router.completion(
            model=settings.llm_model,
            messages=messages,
            temperature=0.3,
            max_tokens=200,
            stream=True,
        )
        print("流式调用开始")
        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
        print("\n流式调用完成")
        print("完整响应:", full_response)
    except Exception as e:
        print("流式调用失败:", str(e))

if __name__ == "__main__":
    print("测试litellm completion方法")
    print("\n1. 非流式调用:")
    asyncio.run(test_litellm_completion())

    print("\n2. 流式调用:")
    asyncio.run(test_litellm_streaming())