"""LLM 调用和流式处理模块

这个模块封装了与 OpenAI API 的交互，提供两种调用模式：
1. 非流式调用 - 等待完整响应后返回
2. 流式调用 - 实时接收 token 并通过回调函数推送
"""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from openai import AsyncOpenAI


class LLMClient:
    """处理 LLM 调用和流式响应的客户端

    属性:
        client: AsyncOpenAI 客户端实例
        model: 使用的模型名称
    """

    def __init__(self, openai_client: AsyncOpenAI, model: str):
        """初始化 LLM 客户端

        参数:
            openai_client: 已配置的 AsyncOpenAI 客户端实例
            model: 使用的模型名称
        """
        self.client = openai_client
        self.model = model

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0,
        max_tokens: int = 1000,
    ) -> str:
        """非流式调用 - 等待完整响应后返回

        参数:
            messages: 对话消息列表
            temperature: 温度参数 (0-2.0)
            max_tokens: 最大输出 token 数

        返回:
            LLM 的完整回复文本
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        emit_token: Callable[[str], Awaitable[None]],
        temperature: float = 0,
        max_tokens: int = 1000,
    ) -> str:
        """流式调用 - 实时接收并推送 token

        参数:
            messages: 对话消息列表
            emit_token: 异步回调函数，用于推送每个 token
            temperature: 温度参数 (0-2.0)
            max_tokens: 最大输出 token 数

        返回:
            LLM 的完整回复文本
        """
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        chunks: List[str] = []
        async for chunk in stream:
            text = chunk.choices[0].delta.content
            if text:
                chunks.append(text)
                await emit_token(text)

        return "".join(chunks)
