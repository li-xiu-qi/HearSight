import json
import os
import re
from typing import Any, Dict, List, Optional

from fastmcp import Client

from .models import ToolCallable


def normalize_input(input_data: Any):
    """解析工具调用输入，支持 JSON 文本或普通字符串。"""
    if isinstance(input_data, str):
        s = input_data.strip()
        # 用正则匹配任意数量反引号包裹的块
        m = re.match(r"^`{3,}\s*(?:\w+)?\n?(.*)\n?`{3,}\s*$", s, re.DOTALL)
        if m:
            s = m.group(1).strip()

        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return {"input": input_data}
    return input_data


def create_tool_wrapper(tools_url, tool_name: str) -> ToolCallable:
    """为工具创建调用包装器，统一处理字符串/JSON 输入。"""

    async def tool_wrapper(input_str: str) -> str:
        try:
            params = normalize_input(input_str)
            client = Client(tools_url)
            async with client:
                result = await client.call_tool(tool_name, params)
                return str(result.data)
        except Exception as e:
            return f"调用工具 '{tool_name}' 时发生错误: {str(e)}"

    return tool_wrapper
