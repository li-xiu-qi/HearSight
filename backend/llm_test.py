"""测试LLM调用中连续消息的处理"""

import asyncio
import openai
from config import settings

async def test_llm_with_consecutive_roles():
    """测试连续多个user和assistant消息"""
    # 直接使用openai sdk
    client = openai.OpenAI(api_key=settings.llm_provider_api_key, base_url=settings.llm_provider_base_url)

    # 模拟连续相同role的消息
    messages = [
        {"role": "system", "content": "你是一个AI助手"},
        {"role": "user", "content": "什么是人工智能？"},
        {"role": "user", "content": "它的发展历史是什么？"},  # 连续user
        {"role": "assistant", "content": "人工智能是计算机科学的一个分支"},
        {"role": "assistant", "content": "它的发展历史可以追溯到1950年代"},  # 连续assistant
        {"role": "user", "content": "它有哪些应用？"}
    ]

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.3,
            max_tokens=200,
        )
        print("成功调用，没有报错")
        print("响应:", response.choices[0].message.content)
    except Exception as e:
        print("调用失败，报错:", str(e))

if __name__ == "__main__":
    print("测试连续相同role的消息:")
    asyncio.run(test_llm_with_consecutive_roles())