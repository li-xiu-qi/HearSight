"""FastMCP 客户端示例

测试连接到本地 MCP 工具服务器（HTTP 模式）。
"""

import asyncio
from fastmcp import Client


async def test_mcp_client():
    """测试 MCP 客户端连接和工具调用。"""

    print("测试 MCP 客户端连接...")

    # 连接到本地 MCP 服务器
    client = Client("http://localhost:8001/mcp")

    try:
        async with client:
            print("✓ 连接到 MCP 服务器成功")

            # 列出可用工具
            tools = await client.list_tools()
            print(f"✓ 可用工具: {[tool.name for tool in tools]}")

            # 调用计算器工具
            print("调用计算器工具...")
            result = await client.call_tool("calculator", {"a": 2.0, "b": 3.0})
            print(f"✓ 计算器结果对象: {result}")
            print(f"✓ 实际结果: {result.data}")
            print(f"✓ 结果类型: {type(result.data)}")

    except Exception as e:
        print(f"✗ 连接或调用失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mcp_client())


if __name__ == "__main__":
    asyncio.run(test_mcp_client())
