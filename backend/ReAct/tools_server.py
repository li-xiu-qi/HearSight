"""本地工具 MCP 服务器

将本地工具函数暴露为 MCP (Model Context Protocol) 工具服务。
"""

import sys
import os

# 添加 backend 目录到路径
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print("backend_path:", backend_path)
sys.path.insert(0, backend_path)
print("sys.path:", sys.path[:3])  # 只打印前3个

try:
    import backend
    print("backend imported successfully")
except ImportError as e:
    print("import backend failed:", e)

from fastmcp import FastMCP

# 导入本地工具
# from tools.calculator import add_numbers  # 示例，已移除
from backend.tools.retrieval_tool import retrieval_tool

# 创建 MCP 服务器
mcp = FastMCP("LocalTools")


@mcp.tool()
async def knowledge_retrieval(question: str, transcript_ids) -> str:
    """知识库检索工具，从指定转录中检索相关内容。

    参数:
        question: 用户问题，字符串类型，用于描述需要检索的具体内容
        transcript_ids: 转录ID，可以是以下格式：
            - 单个整数：如 123，表示从单个视频文件中检索
            - 整数列表：如 [123, 456, 789]，表示从多个视频文件中同时检索
            - 字符串格式的列表：如 "[123, 456]"，会被自动解析为列表

    返回:
        压缩后的关键信息字符串，包含检索到的相关内容、时间戳和文件名信息

    示例:
        knowledge_retrieval("什么是机器学习？", [1, 2, 3])
        knowledge_retrieval("插件功能介绍", 5)
    """
    result = await retrieval_tool.retrieve_knowledge(question, transcript_ids)
    return result


if __name__ == "__main__":
    # 启动 MCP 服务器，使用 HTTP 传输
    mcp.run(transport="http", port=8004)