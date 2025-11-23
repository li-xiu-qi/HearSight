"""Action 解析工具 - 统一处理 ReAct 格式的动作解析"""

import json
import re
from typing import Any, Dict, Optional, Tuple


def parse_response(
    text: str,
) -> Tuple[str, Optional[str], Optional[Dict[str, Any]], Optional[str]]:
    """
    从 LLM 输出解析完整的 ReAct 响应

    解析格式：
    Thought: 思考内容
    Action: 动作名称
    Action Input: {"key": "value"}
    Final Answer: 最终答案

    参数:
        text: LLM 输出的文本

    返回:
        Tuple[thought, action_name, action_input, final_answer]
        - thought: 思考内容
        - action_name: 动作名称
        - action_input: 动作输入字典
        - final_answer: 最终答案
    """
    lines = text.splitlines()

    # 提取 Thought
    thought_line = next((l for l in lines if l.startswith("Thought:")), None)
    thought = (
        thought_line.replace("Thought:", "").strip() if thought_line else ""
    )

    # 提取 Action
    action_line = next((l for l in lines if l.startswith("Action:")), None)
    action_name = None
    if action_line:
        action_name = action_line.replace("Action:", "").strip()

    # 提取 Action Input
    action_input = None
    if action_name:
        input_line = next(
            (l for l in lines if l.startswith("Action Input:")), None
        )
        if input_line:
            try:
                action_input = json.loads(
                    input_line.replace("Action Input:", "").strip()
                )
            except json.JSONDecodeError:
                action_input = {}

    # 提取 Final Answer
    final_answer = None
    if "Final Answer:" in text:
        final_answer = text.split("Final Answer:", 1)[-1].strip()

    return thought, action_name, action_input, final_answer
