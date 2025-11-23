"""ReAct ChatAgent 测试"""

import asyncio
import os
from backend.ReAct import ChatAgent


async def test_chat_agent():
    """测试ChatAgent基本功能"""
    # 使用环境变量或默认配置
    api_key = os.getenv("OPENAI_API_KEY", "your-api-key")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # 创建ChatAgent实例
    agent = ChatAgent(
        openai_api_key=api_key,
        openai_api_base=base_url,
        openai_api_model=model,
        tools_backend_url="http://localhost:8001/mcp"
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