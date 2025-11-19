from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Literal, Optional, Union, cast
from typing_extensions import TypedDict

import aiohttp
import requests
from tenacity import (
    before_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


def on_retry_error(retry_state):
    """重试错误回调：记录详细的错误信息"""
    exception = retry_state.outcome.exception()
    logger.warning(
        f"重试 {retry_state.fn.__name__}，原因：{type(exception).__name__}: {exception}，尝试次数：{retry_state.attempt_number}"
    )


def should_retry(exception):
    """判断是否需要重试的异常条件"""
    if isinstance(
        exception,
        (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError),
    ):
        return True
    if isinstance(exception, requests.HTTPError):
        # 仅对硅基流动 API 的 429 错误进行重试，其他 API 不重试
        if (
            exception.response.status_code == 429
            and "siliconflow" in exception.response.url
        ):
            return True
        return False
    return False


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


def _endpoint(base_url: str) -> str:
    # 统一拼接为 {base}/chat/completions
    return f"{base_url.rstrip('/')}/chat/completions"


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception(should_retry),
    before=before_log(logger, logging.INFO),
    retry_error_callback=on_retry_error,
)
def chat(
    messages: List[ChatMessage],
    api_key: str,
    base_url: str,
    model: str,
    max_tokens: int = 4096,
    timeout: int = 60,
    **kwargs: Any,
) -> str:
    """
    OpenAI 兼容接口：/chat/completions

    messages: 例如 [{"role": "user", "content": "你好"}]
    model: 指定模型名
    max_tokens: 最大输出token数（默认4096）
    timeout: 请求超时时间（秒，默认60）
    kwargs: 透传给接口，例如 temperature, top_p 等

    返回第一条 choice 的 message.content
    """
    url = _endpoint(base_url)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if kwargs:
        payload.update(kwargs)

    r = requests.post(url, json=payload, headers=headers, timeout=timeout)
    # 提供更清晰的错误信息（包含响应体），便于诊断 401/模型未授权等问题
    if not r.ok:
        raise requests.HTTPError(f"{r.status_code} {r.reason}: {r.text}")
    # r.raise_for_status()
    data = r.json()
    # 兼容 OpenAI 风格返回
    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "")


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception(should_retry),
    before=before_log(logger, logging.INFO),
    retry_error_callback=on_retry_error,
)
def chat_with_tools(
    messages: List[Message],
    tools: List[ToolSpec],
    api_key: str,
    base_url: str,
    model: str,
    tool_choice: Optional[Union[Literal["auto", "none"], Dict[str, Any]]] = "auto",
    timeout: int = 60,
    **kwargs: Any,
) -> AssistantMessage:
    """
    OpenAI tools 风格的 Chat 接口。

    - messages: 与 OpenAI 兼容的 messages 列表
    - tools: OpenAI 工具列表（schema 见官方定义）
    - tool_choice: 可选，"auto"/"none"/具体工具对象
    - model: 指定模型名
    - timeout: 请求超时时间（秒，默认60）
    - kwargs: 透传 temperature, top_p 等参数

    返回第一条 choice 的 message（可能包含 tool_calls）。
    """
    url = _endpoint(base_url)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
    }
    if tools:
        payload["tools"] = tools
    if tool_choice is not None:
        payload["tool_choice"] = tool_choice
    if kwargs:
        payload.update(kwargs)

    r = requests.post(url, json=payload, headers=headers, timeout=timeout)
    if not r.ok:
        raise requests.HTTPError(f"{r.status_code} {r.reason}: {r.text}")
    # r.raise_for_status()
    data = r.json()
    # 返回第一条 choice 的 message（含可能的 tool_calls）
    return cast(AssistantMessage, (data.get("choices") or [{}])[0].get("message", {}))


def chat_with_tools_stream(
    messages: List[Message],
    tools: List[ToolSpec],
    api_key: str,
    base_url: str,
    model: str,
    tool_choice: Optional[Union[Literal["auto", "none"], Dict[str, Any]]] = "auto",
    timeout: int = 300,
    **kwargs: Any,
):
    """OpenAI 兼容流式接口。逐行解析 SSE（data: ...）。

    输出对齐常见 SDK 行为：
    - 流式仅输出文本增量：{"type": "text", "delta": str}
    - 工具调用不走流式增量，内部累积，最终在流结束前一次性输出：
      {"type": "tool_calls", "items": [{"id": str|None, "type": "function", "function": {"name": str|None, "arguments": str}}]}
    - 错误：{"type": "error", "message": str}
    - 结束：{"type": "end"}
    """
    url = _endpoint(base_url)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    if tools:
        payload["tools"] = tools
    if tool_choice is not None:
        payload["tool_choice"] = tool_choice
    if kwargs:
        payload.update(kwargs)

    try:
        with requests.post(
            url, json=payload, headers=headers, stream=True, timeout=timeout
        ) as r:
            # 若鉴权失败或其他非 2xx，直接返回一条错误事件，包含响应体，便于定位（避免仅有 401 文案）
            if not r.ok:
                yield {
                    "type": "error",
                    "message": f"{r.status_code} {r.reason}: {r.text}",
                }
                return
            # r.raise_for_status()
            # 工具调用缓冲（按 index 累积）
            tool_buf: dict[int, dict] = {}

            for raw_line in r.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                if raw_line.startswith(":"):
                    # comment line
                    continue
                if not raw_line.startswith("data:"):
                    continue
                data_str = raw_line[len("data:") :].strip()
                if data_str == "[DONE]":
                    # 在结束前输出完整的工具调用（若存在）
                    if tool_buf:
                        items = []
                        for idx in sorted(tool_buf.keys()):
                            t = tool_buf[idx]
                            items.append(
                                {
                                    "id": t.get("id"),
                                    "type": "function",
                                    "function": {
                                        "name": t.get("name"),
                                        # OpenAI 协议此处为字符串，保持一致，由上层决定是否解析 JSON
                                        "arguments": t.get("arguments", ""),
                                    },
                                }
                            )
                        yield {"type": "tool_calls", "items": items}
                    yield {"type": "end"}
                    break
                try:
                    chunk = json.loads(data_str)
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    # 文本增量
                    if delta.get("content"):
                        yield {"type": "text", "delta": delta["content"]}
                    # 工具调用增量（内部累积，不直接对外流出）
                    tool_calls = delta.get("tool_calls") or []
                    for tc in tool_calls:
                        idx = tc.get("index", 0)
                        buf = tool_buf.setdefault(
                            idx, {"id": None, "name": None, "arguments": ""}
                        )
                        tc_id = tc.get("id")
                        if tc_id:
                            buf["id"] = buf["id"] or tc_id
                        fn = tc.get("function") or {}
                        name = fn.get("name")
                        if name:
                            buf["name"] = buf["name"] or name
                        args_delta = fn.get("arguments")
                        if args_delta:
                            buf["arguments"] = (buf.get("arguments") or "") + args_delta
                except Exception as e:
                    yield {"type": "error", "message": f"stream parse error: {e}"}
    except Exception as e:
        # 捕获网络/协议等异常，避免上层 SSE 连接被硬断
        yield {"type": "error", "message": f"stream request error: {e}"}


def chat_text(
    prompt: str,
    api_key: str,
    base_url: str,
    model: str,
    system: Optional[str] = None,
    max_tokens: int = 4096,
    timeout: int = 60,
    **kwargs: Any,
) -> str:
    """
    简洁文本接口：给定 prompt（和可选 system），返回文本回复。

    参数:
    - prompt: 用户输入
    - api_key: API密钥
    - base_url: API基础URL
    - model: 模型名
    - system: 系统提示词
    - max_tokens: 最大输出token数（默认4096）
    - timeout: 请求超时时间（秒，默认60）
    - kwargs: 其他参数
    """
    msgs: List[ChatMessage] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return chat(
        msgs,
        api_key=api_key,
        base_url=base_url,
        model=model,
        max_tokens=max_tokens,
        timeout=timeout,
        **kwargs,
    )


async def chat_text_async(
    prompt: str,
    api_key: str,
    base_url: str,
    model: str,
    system: Optional[str] = None,
    max_tokens: int = 4096,
    timeout: int = 60,
    stream: bool = True,
    **kwargs: Any,
) -> str:
    """
    异步简洁文本接口：给定 prompt（和可选 system），返回文本回复。

    参数:
    - prompt: 用户输入
    - api_key: API密钥
    - base_url: API基础URL
    - model: 模型名
    - system: 系统提示词
    - max_tokens: 最大输出token数（默认4096）
    - timeout: 请求超时时间（秒，默认60）
    - stream: 是否使用流式接收（默认True，更抗超时）
    - kwargs: 其他参数
    """
    msgs: List[ChatMessage] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})

    url = _endpoint(base_url)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": msgs,
        "max_tokens": max_tokens,
        "stream": stream,
    }
    if kwargs:
        payload.update(kwargs)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                if not response.ok:
                    text = await response.text()
                    raise Exception(f"{response.status} {response.reason}: {text}")

                if stream:
                    # 流式接收：逐行读取并拼接内容
                    content = ""
                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if not line or line.startswith("[DONE]"):
                            continue
                        if line.startswith("data: "):
                            line = line[6:]
                        try:
                            chunk = json.loads(line)
                            choice = (chunk.get("choices") or [{}])[0]
                            delta = choice.get("delta", {})
                            if "content" in delta:
                                content += delta["content"]
                        except (json.JSONDecodeError, IndexError, KeyError):
                            pass
                    return content
                else:
                    # 非流式：一次性读取
                    data = await response.json()
                    return (
                        (data.get("choices") or [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
    except asyncio.TimeoutError:
        raise Exception(f"异步请求超时：{timeout}秒")
    except Exception as e:
        logger.error(f"异步聊天请求失败：{e}")
        raise


__all__ = [
    "chat",
    "chat_text",
    "chat_text_async",
    "chat_with_tools",
    "chat_with_tools_stream",
]
