"""本地工具 MCP 服务器

将本地工具函数暴露为 MCP (Model Context Protocol) 工具服务。
"""

import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastmcp import FastMCP

# 导入本地工具
# from tools.calculator import add_numbers  # 示例，已移除
from tools.retrieval_tool import retrieval_tool

# 创建 MCP 服务器
mcp = FastMCP("LocalTools")


@mcp.tool()
async def calculator(a: float, b: float) -> float:
    """计算器工具，计算两个数字的和。

    参数:
        a: 第一个数字
        b: 第二个数字

    返回:
        两数之和
    """
    return a + b


@mcp.tool()
async def knowledge_retrieval(question: str, transcript_id: int) -> str:
    """知识库检索工具，从指定转录中检索相关内容。

    参数:
        question: 用户问题
        transcript_id: 转录ID

    返回:
        压缩后的关键信息字符串
    """
    result = await retrieval_tool.retrieve_knowledge(question, transcript_id)
    return result


if __name__ == "__main__":
    # 启动 MCP 服务器，使用 HTTP 传输
    mcp.run(transport="http", port=8001)