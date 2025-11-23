"""通用 ReAct Agent 基类"""

import asyncio
import contextlib
import json
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from backend.startup import get_llm_router
from backend.config import settings

from .models import AgentResult, StreamCallback, ToolCallable
from .react_loop import ReactLoop
from .tool_manager import ToolManager


class BaseAgent:
    """
    基于 ReAct 范式的通用 Agent 基类

    特性：
    - 支持 ReAct 多步推理
    - 支持结构化输出（trace + 最终答案）
    - 支持流式响应
    - 模块化设计，易于扩展
    """

    def __init__(
        self,
        tools_backend_url: str,
        config_path: Optional[str] = None,
        prompt_builder: Optional[Callable[[List[str], str], str]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ):
        """
        初始化 Agent

        参数:
            tools_backend_url: 工具后端服务 URL
            config_path: 工具配置文件路径
            prompt_builder: 系统提示构建函数
            extra_headers: 额外的 HTTP 请求头
        """
        headers = {"DashScope-Plugin": "optional"}
        if extra_headers:
            headers.update(extra_headers)

        # 使用全局 LLM 路由器和配置
        self.llm_router = get_llm_router()
        self.llm_model = settings.llm_model

        self.tool_manager = ToolManager(tools_backend_url, config_path)

        # 使用提供的 prompt_builder，或使用默认的通用构建器
        if prompt_builder is None:
            prompt_builder = self._default_prompt_builder

        self.react_loop = ReactLoop(
            self.llm_router, self.llm_model, self.tool_manager, prompt_builder
        )

    @staticmethod
    def _default_prompt_builder(
        available_actions: List[str], tool_description: str
    ) -> str:
        """默认的系统提示构建器"""
        allowed_list = ", ".join(available_actions)
        prompt = f"""
        你是一个能干的助手，可以通过调用外部工具来回答问题。

        {tool_description}

        # 格式要求（必须严格遵守）

        1. 你输出时禁止使用 Markdown、禁止加粗、禁止列表、禁止编号。
        2. 你可以多次调用工具来收集信息，直到能够给出最终答案。
        3. 每一步推理只能按照下面这种纯文本格式输出（不要多也不要少）：

        Thought: （这里写你的思考）
        Action: 工具名（必须是下面列表中的一个：{allowed_list}）
        Action Input: （这里是传给工具的参数，如果是 JSON 就直接写 JSON 字符串）

        当你已经拿到足够信息并且可以给出最终答案时，必须输出：

        Thought: （这里说明你已经可以回答问题了）
        Final Answer: （这里直接用自然语言回答用户）

        # 示例

        问题：今天北京的天气怎么样？
        Thought: 用户询问北京天气，我需要调用天气查询工具来获取信息。
        Action: weather_query
        Action Input: {{"city": "北京"}}

        问题：Observation: 北京今天多云，温度15-25℃，空气质量良好。
        Thought: 我已经从天气工具获取到北京的天气信息，可以直接回答用户了。
        Final Answer: 北京今天多云，温度15-25℃，空气质量良好。

        # 注意：
        - 只能输出 "Action:"、"Action Input:"、"Thought:"、"Final Answer:" 这几种前缀。

        现在开始输出
        """
        return prompt.strip()

    async def list_available_tools(self):
        """获取所有可用工具列表（从 MCP 后端）"""
        return await self.tool_manager.list_available_tools()

    async def get_available_tools(
        self, allowed_tools: Optional[List[str]] = None
    ) -> Dict[str, ToolCallable]:
        """
        根据允许的工具列表获取可用的工具字典：名称 -> 调用包装器
        """
        return await self.tool_manager.get_available_tools(allowed_tools)

    async def generate_tool_descriptions(
        self, allowed_tools: Optional[List[str]] = None
    ) -> str:
        """
        根据可用工具生成工具描述（供 SYSTEM_PROMPT 使用）
        """
        return await self.tool_manager.generate_tool_descriptions(
            allowed_tools
        )

    async def generate_answer(
        self,
        question: str,
        allowed_tools: Optional[List[str]] = None,
    ) -> AgentResult:
        """
        生成答案（非流式模式）

        参数:
            question: 用户问题
            allowed_tools: 允许使用的工具列表，如果为None则从配置文件加载

        返回:
            AgentResult 包含最终答案、推理步骤、消息历史和错误信息
        """
        return await self.react_loop.run(question, allowed_tools)

    async def stream_answer(
        self,
        question: str,
        allowed_tools: Optional[List[str]] = None,
    ) -> AsyncIterator[str]:
        """
        流式生成答案（支持客户端流式接收）

        参数:
            question: 用户问题
            allowed_tools: 允许使用的工具列表，如果为None则从配置文件加载

        产出:
            SSE 格式的事件流
        """
        queue: asyncio.Queue[Optional[Dict[str, Any]]] = asyncio.Queue()

        async def enqueue(event: Dict[str, Any]):
            await queue.put(event)

        async def runner():
            result = await self.react_loop.run(
                question, allowed_tools, enqueue
            )
            await queue.put(
                {
                    "type": "complete",
                    "data": {
                        "final_answer": result.final_answer,
                        "error": result.error,
                    },
                }
            )
            await queue.put(None)

        task = asyncio.create_task(runner())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield self._format_sse_event(event)
        except asyncio.CancelledError:
            task.cancel()
            raise
        finally:
            if not task.done():
                task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    @staticmethod
    def _format_sse_event(event: Dict[str, Any]) -> str:
        """格式化 SSE 事件"""
        event_type = event.get("type", "message")
        data = event.get("data", {})
        payload = json.dumps(data, ensure_ascii=False)
        return f"event: {event_type}\ndata: {payload}\n\n"
