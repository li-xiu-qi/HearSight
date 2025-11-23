# -*- coding: utf-8 -*-
"""litellm 示例测试"""

import sys
import os

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import litellm
from litellm import Router
from backend.config import settings

def test_litellm():
    """测试 litellm 调用"""

    # 参数
    model = f"{settings.llm_provider}/{settings.llm_model}"
    api_key = settings.llm_provider_api_key
    base_url = settings.llm_provider_base_url
    tpm = settings.llm_tpm
    rpm = settings.llm_rpm

    model_list = [{
        "model_name": settings.llm_model,
        "litellm_params": {
            "model": model,
            "api_key": api_key,
            "base_url": base_url,
            "tpm": tpm,
            "rpm": rpm,
        }
    }]

    router = Router(model_list=model_list)

    messages = [{"role": "user", "content": "请总结这个视频的内容"}]

    print("=== 测试 litellm Router 调用 ===")
    print(f"模型: {model}")
    print(f"base_url: {base_url}")
    print(f"tpm: {tpm}, rpm: {rpm}")

    try:
        response = router.completion(
            model=settings.llm_model,
            messages=messages,
        )

        print("响应成功:")
        print(response.choices[0].message.content)

    except Exception as e:
        print(f"调用失败: {e}")

def test_litellm_stream():
    """测试 litellm Router 流式调用"""

    # 参数
    model = f"{settings.llm_provider}/{settings.llm_model}"
    api_key = settings.llm_provider_api_key
    base_url = settings.llm_provider_base_url
    tpm = settings.llm_tpm
    rpm = settings.llm_rpm

    model_list = [{
        "model_name": settings.llm_model,
        "litellm_params": {
            "model": model,
            "api_key": api_key,
            "base_url": base_url,
            "tpm": tpm,
            "rpm": rpm,
        }
    }]

    router = Router(model_list=model_list)

    messages = [{"role": "user", "content": "请总结这个视频的内容"}]

    print("=== 测试 litellm Router 流式调用 ===")
    print(f"模型: {model}")
    print(f"base_url: {base_url}")
    print(f"tpm: {tpm}, rpm: {rpm}")

    try:
        response = router.completion(
            model=settings.llm_model,
            messages=messages,
            stream=True,
        )

        print("流式响应:")
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
        print("\n流式完成")

    except Exception as e:
        print(f"调用失败: {e}")

if __name__ == "__main__":
    test_litellm()
    print()
    test_litellm_stream()