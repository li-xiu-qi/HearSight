"""通用工具管理模块"""

import json
import os
from typing import Any, Dict, List, Optional

from fastmcp import Client

from .models import ToolCallable
from .utils import create_tool_wrapper


class ToolManager:
    """
    负责工具列表、工具配置和工具描述的管理。

    主要功能：
    - 从 MCP 服务获取可用工具列表
    - 管理工具配置和权限控制
    - 生成工具描述文本供 LLM 使用
    - 创建工具调用包装器
    """

    def __init__(self, tools_url: str, config_path: Optional[str] = None):
        """
        初始化工具管理器。

        参数:
            tools_url: MCP 工具后端服务的 URL
            config_path: 工具配置文件路径（JSON 数组格式）
        """
        self.tools_url = tools_url
        self.config_path = config_path

    async def list_available_tools(self):
        """
        直接从 MCP 服务端获取工具列表。

        通过 FastMCP 客户端连接到工具后端服务，
        获取所有注册的工具信息。
        """
        client = Client(self.tools_url)
        async with client:
            return await client.list_tools()

    def load_tool_config(self) -> List[str]:
        """
        从配置文件加载允许使用的工具列表。

        文件格式：JSON 数组，包含允许的工具名称

        返回:
            允许的工具名称列表，如果文件不存在或格式错误则返回空列表
        """
        if self.config_path is None:
            return []

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                if isinstance(config, list):
                    return config
        except FileNotFoundError:
            print(f"工具配置文件未找到: {self.config_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"工具配置文件格式错误: {e}")
            return []

        return []

    def get_allowed_tools(
        self, allowed_tools: Optional[List[str]] = None
    ) -> List[str]:
        """
        获取允许使用的工具列表。

        如果提供了 allowed_tools 参数，直接返回；
        否则从配置文件加载默认的允许工具列表。
        """
        if allowed_tools is not None:
            return allowed_tools
        return self.load_tool_config()

    async def get_available_tools(
        self, allowed_tools: Optional[List[str]] = None
    ) -> Dict[str, ToolCallable]:
        """
        根据允许的工具列表获取可用的工具字典：名称 -> 调用包装器。

        这个方法会：
        1. 从 MCP 服务获取所有可用工具
        2. 根据配置过滤出允许的工具
        3. 为每个工具创建调用包装器
        """
        all_tools = await self.list_available_tools()
        allowed_tool_names = set(self.get_allowed_tools(allowed_tools))

        available_tools: Dict[str, ToolCallable] = {}
        for tool in all_tools:
            if tool.name in allowed_tool_names:
                available_tools[tool.name] = create_tool_wrapper(
                    self.tools_url, tool.name
                )

        return available_tools

    async def generate_tool_descriptions(
        self, allowed_tools: Optional[List[str]] = None
    ) -> str:
        """
        根据可用工具生成工具描述（供 SYSTEM_PROMPT 使用）

        生成的描述包含工具名称、功能说明和参数信息，
        帮助 LLM 了解如何调用这些工具。
        """
        all_tools = await self.list_available_tools()
        allowed_tool_names = set(self.get_allowed_tools(allowed_tools))

        # 如果没有允许的工具，返回提示信息
        if not allowed_tool_names:
            return "## 工具\n当前没有配置可用的工具。你不能调用任何外部工具，只能基于已有对话回答问题。"

        descriptions = ["## 工具", "你有以下可用的工具："]

        # 为每个允许的工具生成详细描述
        for i, tool in enumerate(all_tools, 1):
            if tool.name not in allowed_tool_names:
                continue

            # 添加工具基本信息
            descriptions.append(f"{i}. **{tool.name}**")
            descriptions.append(f"   * **描述**: {tool.description}")

            # 解析工具的参数模式
            schema = getattr(tool, "inputSchema", None)
            if schema and isinstance(schema, dict) and "properties" in schema:
                params = []
                required_fields = set(schema.get("required", []))

                # 处理每个参数
                for param_name, param_info in schema["properties"].items():
                    param_type = param_info.get("type", "unknown")
                    param_desc = param_info.get("description", "")
                    required = param_name in required_fields
                    req_marker = " (必需)" if required else " (可选)"
                    params.append(
                        f"- `{param_name}` ({param_type}){req_marker}: {param_desc}"
                    )

                # 添加参数列表
                if params:
                    descriptions.append("   * **参数**:")
                    descriptions.extend([f"     {p}" for p in params])

            descriptions.append("")

        return "\n".join(descriptions)
