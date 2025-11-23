"""基于ReAct的聊天Agent"""

import os
from typing import List, Optional
from .base_agent import BaseAgent
from .chat_prompt_builder import build_chat_agent_system_prompt


class ChatAgent(BaseAgent):
    """
    基于ReAct的聊天Agent

    专门用于处理聊天对话，支持知识库检索和多轮对话。
    """

    def __init__(
        self,
        openai_api_key: str,
        openai_api_base: str,
        openai_api_model: str,
        tools_backend_url: str = "http://localhost:8001/mcp",
    ):
        """
        初始化聊天Agent

        参数:
            openai_api_key: OpenAI API 密钥
            openai_api_base: OpenAI API 基础 URL
            openai_api_model: 使用的模型名称
            tools_backend_url: 工具后端服务 URL
        """
        # 构建配置文件路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "chat_tools_config.json")

        super().__init__(
            openai_api_key=openai_api_key,
            openai_api_base=openai_api_base,
            openai_api_model=openai_api_model,
            tools_backend_url=tools_backend_url,
            config_path=config_path,
            prompt_builder=build_chat_agent_system_prompt,
            extra_headers={"DashScope-Plugin": "optional"},
        )

    async def chat_with_transcript(
        self,
        question: str,
        transcript_id: int,
        allowed_tools: Optional[List[str]] = None
    ) -> str:
        """
        与单个转录内容进行聊天

        参数:
            question: 用户问题
            transcript_id: 转录ID
            allowed_tools: 允许使用的工具列表

        返回:
            聊天回答
        """
        # 设置默认允许的工具
        if allowed_tools is None:
            allowed_tools = ["knowledge_retrieval"]

        # 构建问题上下文
        context_question = f"请基于转录ID {transcript_id} 的内容回答：{question}"

        # 执行ReAct推理
        result = await self.generate_answer(
            question=context_question,
            allowed_tools=allowed_tools
        )

        return result.final_answer

    async def chat_with_multiple_transcripts(
        self,
        question: str,
        transcript_ids: List[int],
        allowed_tools: Optional[List[str]] = None
    ) -> str:
        """
        与多个转录内容进行聊天

        参数:
            question: 用户问题
            transcript_ids: 转录ID列表
            allowed_tools: 允许使用的工具列表

        返回:
            聊天回答
        """
        if allowed_tools is None:
            allowed_tools = ["knowledge_retrieval"]

        # 为每个transcript_id执行检索和整合
        context_parts = []
        for transcript_id in transcript_ids:
            result = await self.generate_answer(
                question=f"请基于转录ID {transcript_id} 的内容回答：{question}",
                allowed_tools=allowed_tools
            )
            if result.final_answer and "error" not in result.final_answer.lower():
                context_parts.append(f"转录 {transcript_id}: {result.final_answer}")

        if not context_parts:
            return "抱歉，在选定的转录中没有找到相关信息。"

        # 整合多个转录的回答
        combined_context = "\n".join(context_parts)
        final_result = await self.generate_answer(
            question=f"基于以下多个转录的内容回答问题：\n{combined_context}\n\n原问题：{question}",
            allowed_tools=[]
        )

        return final_result.final_answer