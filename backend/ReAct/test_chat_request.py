"""测试ChatAgent的功能"""

import asyncio
import sys
import os

# 添加backend目录到路径
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from backend.config import settings
from ReAct.chat_agent import ChatAgent

async def test_chat_agent():
    """测试ChatAgent的generate_answer方法"""
    # 创建ChatAgent实例
    chat_agent = ChatAgent(
        openai_api_key=settings.llm_provider_api_key,
        openai_api_base=settings.llm_provider_base_url,
        openai_api_model=settings.llm_model,
        tools_backend_url="http://localhost:8004/mcp"
    )

    question = "我们目前的视频里面都有介绍了多少Obsidian插件？"
    transcript_ids = [5, 4, 3, 2, 1]

    try:
        # 调用generate_answer，传入transcript_ids
        result = await chat_agent.generate_answer(question, allowed_tools=None, transcript_ids=transcript_ids)

        print("ChatAgent调用成功")
        print("最终答案:", result.final_answer)
        print("推理步骤数量:", len(result.trace))
        print("消息历史长度:", len(result.messages))

        # 打印推理轨迹
        for step in result.trace:
            print(f"步骤 {step.step}: {step.thought}")
            if step.action:
                print(f"  动作: {step.action}")
            if step.observation:
                print(f"  观察: {step.observation}")

    except Exception as e:
        print("ChatAgent调用失败:", str(e))

if __name__ == "__main__":
    print("测试ChatAgent功能:")
    asyncio.run(test_chat_agent())