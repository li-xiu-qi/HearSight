from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union, Literal, TypedDict, cast

import requests

from config import get_config


# === 类型声明（OpenAI 兼容）===
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

def _openai_settings() -> Tuple[str, str, str]:
    """
    返回 (api_key, base_url, default_model)
    仅支持最新结构：
    - cfg["chat_server"]["openai"] 下包含 api_key/base_url/chat_model
    不做 try/except，缺字段让其抛错，便于定位问题。
    """
    cfg = get_config()
    z = cfg["chat_server"]["openai"]
    api_key: str = z["api_key"]
    base_url: str = z["base_url"]
    default_model: str = z["chat_model"]
    return api_key, base_url, default_model


def _endpoint(base_url: str) -> str:
    # 统一拼接为 {base}/chat/completions
    return f"{base_url.rstrip('/')}/chat/completions"



def chat(
    messages: List[ChatMessage],
    model: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    OpenAI 兼容接口：/chat/completions

    messages: 例如 [{"role": "user", "content": "你好"}]
    model: 不传则使用配置中的 chat_model
    kwargs: 透传给接口，例如 temperature, top_p 等

    返回第一条 choice 的 message.content
    """
    api_key, base_url, default_model = _openai_settings()
    use_model = model or default_model

    url = _endpoint(base_url)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": use_model,
        "messages": messages,
    }
    if kwargs:
        payload.update(kwargs)

    r = requests.post(url, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    data = r.json()
    # 兼容 OpenAI 风格返回
    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "")


def chat_with_tools(
    messages: List[Message],
    tools: List[ToolSpec],
    tool_choice: Optional[Union[Literal["auto", "none"], Dict[str, Any]]] = "auto",
    model: Optional[str] = None,
    **kwargs: Any,
) -> AssistantMessage:
    """
    OpenAI tools 风格的 Chat 接口。

    - messages: 与 OpenAI 兼容的 messages 列表
    - tools: OpenAI 工具列表（schema 见官方定义）
    - tool_choice: 可选，"auto"/"none"/具体工具对象
    - model: 不传则使用配置中的默认 chat_model
    - kwargs: 透传 temperature, top_p 等参数

    返回第一条 choice 的 message（可能包含 tool_calls）。
    """
    api_key, base_url, default_model = _openai_settings()
    use_model = model or default_model

    url = _endpoint(base_url)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": use_model,
        "messages": messages,
        "tools": tools,
    }
    if tool_choice is not None:
        payload["tool_choice"] = tool_choice
    if kwargs:
        payload.update(kwargs)

    r = requests.post(url, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    data = r.json()
    # 返回第一条 choice 的 message（含可能的 tool_calls）
    return cast(AssistantMessage, (data.get("choices") or [{}])[0].get("message", {}))


def chat_text(
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    简洁文本接口：给定 prompt（和可选 system），返回文本回复。
    """
    msgs: List[ChatMessage] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return chat(msgs, model=model, **kwargs)


__all__ = [
    "chat",
    "chat_text",
    "chat_with_tools",
]
