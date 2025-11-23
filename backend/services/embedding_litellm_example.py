# -*- coding: utf-8 -*-
"""litellm embedding 示例测试"""

import sys
import os
import asyncio

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import litellm
from litellm import Router
from backend.config import settings
from backend.startup import get_embedding_router

async def test_litellm_embedding():
    """测试 litellm embedding 调用"""

    router = get_embedding_router()

    input_text = "请总结这个视频的内容"

    print("=== 测试 litellm Router embedding 调用 ===")
    print(f"模型: {settings.embedding_model}")
    print(f"base_url: {settings.embedding_provider_base_url}")

    try:
        response = await router.aembedding(
            model=settings.embedding_model,
            input=input_text
        )

        print("embedding 响应成功:")
        print(f"response type: {type(response)}")
        print(f"data type: {type(response.data)}")
        print(f"data[0] type: {type(response.data[0])}")
        embedding_vector = response.data[0]['embedding']
        print(f"向量维度: {len(embedding_vector)}")
        print(f"前5个值: {embedding_vector[:5]}")

    except Exception as e:
        print(f"调用失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_litellm_embedding())
