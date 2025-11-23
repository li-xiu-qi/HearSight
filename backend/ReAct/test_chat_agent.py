"""ReAct ChatAgent 测试"""

import asyncio
import sys
import os

# 添加backend目录到路径
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
parent_path = os.path.abspath(os.path.join(backend_path, '..'))
for path in [backend_path, parent_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

from backend.config import settings
from backend.ReAct import ChatAgent


async def test_chat_agent():
    """测试ChatAgent基本功能"""
    # 使用settings配置
    agent = ChatAgent(
        openai_api_key=settings.llm_provider_api_key,
        openai_api_base=settings.llm_provider_base_url,
        openai_api_model=settings.llm_model,
        tools_backend_url="http://localhost:8004/mcp"
    )

    # 测试基本功能
    try:
        # 测试列出工具
        tools = await agent.list_available_tools()
        print(f"可用工具: {[tool.name for tool in tools]}")

        # 测试生成工具描述
        tool_desc = await agent.generate_tool_descriptions()
        print(f"工具描述:\n{tool_desc}")

        print("ChatAgent初始化成功")

    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_chat_agent())