# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Literal, TypedDict


class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ToolFunction(TypedDict, total=False):
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolSpec(TypedDict):
    type: Literal["function"]
    function: ToolFunction


class ToolCallFunction(TypedDict):
    name: str
    arguments: str


class ToolCall(TypedDict, total=False):
    id: str
    type: Literal["function"]
    function: ToolCallFunction


class AssistantMessage(TypedDict, total=False):
    role: Literal["assistant"]
    content: str
    tool_calls: List[ToolCall]


Message = Union[ChatMessage, AssistantMessage]
