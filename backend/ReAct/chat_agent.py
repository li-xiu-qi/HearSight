"""基于ReAct的聊天Agent"""

import os
from typing import List, Optional
from .base_agent import BaseAgent
from .chat_prompt_builder import build_chat_agent_system_prompt
from .memory_manager import MemoryManager
from .react_loop import ReactLoop


class ChatAgent(BaseAgent):
    """
    基于ReAct的聊天Agent

    专门用于处理聊天对话，支持知识库检索和多轮对话。
    """

    def __init__(
        self,
        tools_backend_url: str = "http://localhost:8004/mcp",
    ):
        """
        初始化聊天Agent

        参数:
            tools_backend_url: 工具后端服务 URL
        """
        # 构建配置文件路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "chat_tools_config.json")

        super().__init__(
            tools_backend_url=tools_backend_url,
            config_path=config_path,
            prompt_builder=build_chat_agent_system_prompt,
            extra_headers={"DashScope-Plugin": "optional"},
        )

        # 初始化记忆管理器
        self.memory_manager = MemoryManager()

    async def generate_answer(
        self,
        question: str,
        allowed_tools: Optional[List[str]] = None,
        transcript_ids: Optional[List[int]] = None,
    ):
        """
        生成答案（支持记忆管理）

        参数:
            question: 用户问题
            allowed_tools: 允许使用的工具列表
            transcript_ids: 用户选择的转录ID列表

        返回:
            AgentResult 包含最终答案、推理步骤、消息历史和错误信息
        """
        # 检查是否需要总结记忆
        if self.memory_manager.should_summarize():
            await self._summarize_memory()

        # 添加用户问题到记忆
        self.memory_manager.add_message({"role": "user", "content": question})

        # 获取当前上下文消息
        context_messages = self.memory_manager.get_context_messages()

        # 创建包含transcript_ids的prompt_builder
        def prompt_builder_with_transcript_ids(action_names, tool_description):
            return build_chat_agent_system_prompt(action_names, tool_description, transcript_ids)

        # 创建临时的ReactLoop，使用自定义prompt_builder
        temp_react_loop = ReactLoop(
            self.llm_router, self.llm_model, self.tool_manager, prompt_builder_with_transcript_ids
        )

        # 调用ReactLoop.run，但需要传入正确的参数
        # 注意：这里需要修改以使用记忆管理的上下文
        result = await temp_react_loop.run(question, allowed_tools)

        # 添加助手回复到记忆
        if result.final_answer:
            self.memory_manager.add_message({"role": "assistant", "content": result.final_answer})

        return result

    async def _summarize_memory(self) -> None:
        """
        总结记忆
        """
        await self.memory_manager.summarize_memory()
        