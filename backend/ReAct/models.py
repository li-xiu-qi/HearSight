"""ReAct 核心数据模型定义"""

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional

# 类型别名
ToolCallable = Callable[[str], Awaitable[str]]
StreamCallback = Callable[[Dict[str, Any]], Awaitable[None]]


@dataclass
class TraceStep:
    """ReAct 推理步骤"""

    step: int  # 第几步
    thought: str  # Thought 内容
    action: Optional[str] = (
        None  # 执行的动作名称（如 generate_sql、execute_query）
    )
    action_input: Optional[Dict[str, Any]] = None  # 动作输入
    observation: Optional[str] = None  # 动作执行结果
    raw_response: str = ""  # LLM 的完整输出


@dataclass
class AgentResult:
    """Agent 执行结果"""

    final_answer: str  # 最终回答
    trace: List[TraceStep]  # 推理步骤列表
    messages: List[Dict[str, str]]  # 消息历史
    error: Optional[str] = None  # 错误信息
