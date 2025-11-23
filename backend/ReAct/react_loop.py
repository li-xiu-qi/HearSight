"""
ReAct 推理循环模块

这个模块实现了基于 ReAct (Reasoning + Acting) 范式的推理循环机制。
ReAct 是一种让大语言模型通过交替进行推理(Reasoning)和行动(Acting)来解决复杂问题的技术。

核心工作流程：
1. 接收用户问题
2. 初始化推理上下文（系统提示、工具描述等）
3. 进入推理循环：
   - 调用 LLM 生成推理步骤（Thought + Action/Action Input）
   - 解析 LLM 响应，提取思考内容和动作指令
   - 如果是最终答案，直接返回结果
   - 如果需要执行动作，调用相应工具并获取观察结果
   - 将观察结果反馈给 LLM，继续下一轮推理
4. 循环直到达到最大步数或得到最终答案

支持功能：
- 流式响应：实时输出推理过程和结果
- 工具集成：通过 ToolManager 管理外部工具调用
- 错误处理：完善的异常捕获和错误信息返回
- 推理追踪：记录完整的推理步骤用于调试和分析
"""

import json
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from .action_parser import parse_response
from .actions import ActionExecutor
from .models import AgentResult, StreamCallback, ToolCallable, TraceStep


class ReactLoop:
    """
    处理 ReAct 推理循环的核心类

    这个类封装了完整的 ReAct 推理过程，负责协调 LLM 调用、工具执行、
    结果解析和流式响应等各个环节。

    主要职责：
    - 管理推理循环的执行流程
    - 处理 LLM 响应解析和动作执行
    - 维护推理状态和消息历史
    - 支持流式输出和错误处理
    """

    def __init__(
        self,
        llm_client: Any,
        tool_manager: Any,
        prompt_builder: Callable[[List[str], str], str],
        max_loops: int = 10,
    ):
        """
        初始化 ReAct 循环处理器

        参数:
            llm_client: LLM 客户端实例，用于调用大语言模型
            tool_manager: 工具管理器实例，负责工具的加载和调用
            prompt_builder: 系统提示构建函数，根据可用工具生成提示文本
            max_loops: 最大推理循环次数，防止无限循环，默认10次
        """
        self.llm_client = llm_client
        self.tool_manager = tool_manager
        self.prompt_builder = prompt_builder
        # 创建动作执行器，传入 LLM 客户端（用于可能的内部动作处理）
        self.action_executor = ActionExecutor(llm_client)
        self.max_loops = max_loops

    async def run(
        self,
        question: str,
        allowed_tools: Optional[List[str]] = None,
        stream_callback: Optional[StreamCallback] = None,
    ) -> AgentResult:
        """
        执行完整的 ReAct 推理循环

        这个方法实现了 ReAct 范式的核心循环：
        1. 初始化推理上下文
        2. 循环调用 LLM 和执行工具
        3. 直到得到最终答案或达到最大循环次数

        参数:
            question: 用户输入的问题或指令
            allowed_tools: 允许使用的工具名称列表，如果为None则使用默认配置
            stream_callback: 流式回调函数，用于实时输出推理过程
                          如果提供此函数，将启用流式模式

        返回:
            AgentResult: 包含最终答案、推理轨迹、消息历史和可能的错误信息

        异常:
            所有异常都会被捕获并包装在 AgentResult 中返回，不会抛出
        """
        # 初始化推理轨迹和消息历史
        # trace: 记录每次推理步骤的详细信息，用于调试和分析
        trace: List[TraceStep] = []
        # messages: 完整的对话历史，包含系统提示、用户问题、助手回复和工具结果
        messages: List[Dict[str, str]] = []

        # 定义内部辅助函数：发送事件到流式回调
        async def emit(event_type: str, payload: Dict[str, Any]):
            """
            向流式回调发送事件

            参数:
                event_type: 事件类型，如 'thought', 'action', 'observation', 'final_answer', 'error'
                payload: 事件数据字典
            """
            if stream_callback:
                await stream_callback({"type": event_type, "data": payload})

        # 定义内部辅助函数：发送 token 块（用于流式输出）
        async def emit_token_chunk(content: str):
            """
            发送 LLM 生成的 token 块到流式回调

            参数:
                content: 新生成的文本内容
            """
            if content:
                await emit("token", {"content": content})

        # 根据是否启用流式模式设置 token 回调
        token_callback = emit_token_chunk if stream_callback else None

        try:
            # ===== 第一阶段：准备推理上下文 =====

            # 获取可用的工具字典（名称 -> 调用函数的映射）
            available_tools = await self.tool_manager.get_available_tools(
                allowed_tools
            )

            # 获取允许的外部工具名称列表
            external_tools = self.tool_manager.get_allowed_tools(allowed_tools)
            # 构建完整的可用动作列表：外部工具 + 内置的 'finish' 动作
            # 'finish' 是元动作，用于表示推理结束并给出最终答案
            available_actions = external_tools + ["finish"]

            # 生成工具描述文本，用于构建系统提示
            tool_description = (
                await self.tool_manager.generate_tool_descriptions(
                    allowed_tools
                )
            )

            # 使用提示构建器生成系统提示
            # 系统提示包含工具使用说明和格式要求
            system_prompt = self.prompt_builder(
                available_actions, tool_description
            )

            # 初始化对话消息历史
            messages = [
                {"role": "system", "content": system_prompt},  # 系统指令
                {"role": "user", "content": question},  # 用户问题
            ]

            # ===== 第二阶段：执行推理循环 =====

            max_loops = self.max_loops  # 最大循环次数
            step_index = 0  # 当前步骤编号

            # 开始 ReAct 推理循环
            for loop_count in range(max_loops):
                step_index = loop_count + 1  # 步骤编号从1开始

                # 调用 LLM 生成推理步骤
                # 根据是否启用流式模式选择不同的调用方式
                if token_callback:
                    # 流式调用：实时接收 token 并通过回调推送
                    response_text = (
                        await self.llm_client.chat_completion_stream(
                            messages,
                            emit_token=token_callback,  # 实时推送 token
                            temperature=0.2,  # 较低温度保证推理稳定性
                            max_tokens=800,  # 限制输出长度
                        )
                    )
                else:
                    # 非流式调用：等待完整响应
                    response_text = await self.llm_client.chat_completion(
                        messages,
                        temperature=0.2,  # 较低温度保证推理稳定性
                        max_tokens=800,  # 限制输出长度
                    )

                # 将 LLM 响应添加到消息历史中
                messages.append(
                    {"role": "assistant", "content": response_text}
                )

                # ===== 第三阶段：解析 LLM 响应 =====

                # 使用 action_parser 解析响应，提取结构化信息
                # 返回：思考内容、动作名称、动作输入参数、最终答案
                thought, action_name, action_input, final_answer_text = (
                    parse_response(response_text)
                )

                # 发送思考过程到流式回调（如果启用）
                if thought:
                    await emit(
                        "thought", {"step": step_index, "content": thought}
                    )

                # ===== 第四阶段：检查是否得到最终答案 =====

                # 如果 LLM 给出了最终答案，推理结束
                if final_answer_text:
                    # 记录推理步骤到轨迹
                    trace.append(
                        TraceStep(
                            step=step_index,
                            thought=thought,
                            action=None,  # 最终答案步骤没有动作
                            action_input=None,  # 最终答案步骤没有动作输入
                            observation=None,  # 最终答案步骤没有观察结果
                            raw_response=response_text,  # 保存原始响应用于调试
                        )
                    )
                    # 发送最终答案到流式回调
                    await emit(
                        "final_answer",
                        {"step": step_index, "content": final_answer_text},
                    )
                    # 返回完整的推理结果
                    return AgentResult(
                        final_answer=final_answer_text,
                        trace=trace,
                        messages=messages,
                        error=None,
                    )

                # ===== 第五阶段：执行动作 =====

                # 如果解析到了动作名称，需要执行相应的工具
                if action_name:
                    # 发送动作执行信息到流式回调
                    await emit(
                        "action",
                        {
                            "step": step_index,
                            "name": action_name,
                            "input": action_input,
                        },
                    )

                    # 调用动作执行器执行工具
                    observation = await self.action_executor.execute_action(
                        action_name,  # 工具名称
                        action_input,  # 工具输入参数
                        available_tools,  # 可用的工具字典
                    )

                    # 记录完整的推理步骤到轨迹
                    trace.append(
                        TraceStep(
                            step=step_index,
                            thought=thought,
                            action=action_name,
                            action_input=action_input,
                            observation=observation,
                            raw_response=response_text,
                        )
                    )

                    # 发送观察结果到流式回调
                    await emit(
                        "observation",
                        {"step": step_index, "content": observation},
                    )

                    # 将观察结果作为用户消息添加到对话历史
                    # 这样 LLM 可以在下一轮推理中使用这个信息
                    messages.append(
                        {
                            "role": "user",
                            "content": f"Observation: {observation}",
                        }
                    )
                else:
                    # ===== 第六阶段：处理解析失败的情况 =====

                    # 如果无法解析动作，说明 LLM 响应格式不正确
                    observation = (
                        "Observation: 响应格式不正确，请遵循指定格式。"
                    )

                    # 记录错误步骤到轨迹
                    trace.append(
                        TraceStep(
                            step=step_index,
                            thought=thought,
                            action=None,
                            action_input=None,
                            observation=observation,
                            raw_response=response_text,
                        )
                    )

                    # 发送错误信息到流式回调
                    await emit(
                        "error", {"step": step_index, "message": observation}
                    )
                    # 将错误信息添加到消息历史，继续下一轮推理
                    messages.append({"role": "user", "content": observation})

            # ===== 第七阶段：循环结束处理 =====

            # 如果达到最大循环次数仍未得到答案，返回超时错误
            final_answer = "抱歉，我无法在有限的步骤内得到最终答案。"
            await emit("error", {"message": final_answer})
            return AgentResult(
                final_answer=final_answer,
                trace=trace,
                messages=messages,
                error="max_loops_exceeded",  # 错误类型标识
            )

        # ===== 第八阶段：异常处理 =====

        except Exception as exc:
            # 捕获所有异常，防止程序崩溃
            error_msg = f"Agent 执行出错: {exc}"
            # 发送错误信息到流式回调
            await emit("error", {"message": error_msg})
            # 返回包含错误信息的 AgentResult
            return AgentResult(
                final_answer="",  # 没有最终答案
                trace=trace,  # 返回已有的推理轨迹
                messages=messages,  # 返回消息历史
                error=error_msg,  # 错误详细信息
            )
