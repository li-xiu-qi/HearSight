"""动作执行模块"""

import json
from typing import Any, Dict

from .models import ToolCallable


class ActionExecutor:
    """执行各个动作"""

    def __init__(self, llm_router: Any, llm_model: str):
        self.llm_router = llm_router
        self.llm_model = llm_model

    async def execute_action(
        self,
        action_name: str,
        action_input: Dict[str, Any],
        available_tools: Dict[str, ToolCallable],
    ) -> str:
        """
        执行指定的动作

        参数:
            action_name: 动作名称
            action_input: 动作输入参数
            available_tools: 可用工具字典

        返回:
            动作执行结果
        """
        # 内部动作 - 不需要外部工具，直接处理
        if action_name == "finish":
            return await self._action_finish(action_input)

        # 外部工具 - 检查是否在可用工具字典中
        if action_name not in available_tools:
            return f"未知工具: {action_name}"

        # 执行外部工具
        return await self._execute_tool(
            action_name, action_input, available_tools
        )

    async def _execute_tool(
        self,
        tool_name: str,
        action_input: Dict[str, Any],
        available_tools: Dict[str, ToolCallable],
    ) -> str:
        """
        执行外部工具

        参数:
            tool_name: 工具名称
            action_input: 动作输入参数
            available_tools: 可用工具字典
        """
        try:
            # 将输入参数序列化为 JSON 字符串传递给工具
            result = await available_tools[tool_name](json.dumps(action_input))

            if not result:
                return "工具执行未返回结果"

            return result
        except Exception as e:
            return f"工具执行失败: {str(e)}"

    async def _action_finish(self, action_input: Dict[str, Any]) -> str:
        """
        结束动作 - 返回最终答案

        参数:
            action_input: 包含 'answer' 的字典
        """
        answer = action_input.get("answer", "")
        return answer
