"""
长文本主题分块（由大模型决定边界）。

用法：
- 调用 segment_text_to_file(text, out_json_path, model=None)；
- 大模型返回每个主题的起止字符索引（左闭右开，方便 Python 切片）；
- 按索引从原始 text 中切出 content，最终写入 JSON 文件。

注意：
- 本模块不使用本地 token 拆分；
- 索引基于传入的原始 text（字符级）；
- 仅做必要的校验与处理，保持最小实现。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict
import json

from backend.chat_utils.chat_client import chat


class TopicSpan(TypedDict):
    """主题片段的基础结构（由大模型返回）。"""
    topic_description: str
    start_char_idx: int  # 起始索引（含）
    end_char_idx: int    # 结束索引（不含）


class TopicSpanWithContent(TopicSpan):
    """带正文内容的主题片段（用于最终输出）。"""
    content: str


def _build_prompt(text: str) -> str:
    """构造提示词：让大模型对整段文本做主题分块并给出字符索引。"""
    example_json = (
        '{\n'
        '  "topic_list": [\n'
        '    {\n'
        '      "topic_description": "主题概述 A",\n'
        '      "start_char_idx": 0,\n'
        '      "end_char_idx": 120\n'
        '    },\n'
        '    {\n'
        '      "topic_description": "主题概述 B",\n'
        '      "start_char_idx": 120,\n'
        '      "end_char_idx": 260\n'
        '    }\n'
        '  ]\n'
        '}'
    )

    instructions = (
        "你将收到一段较长文本，请按语义将其分成若干主题片段，并返回每个片段在原文中的字符起止索引。\n"
        "要求：\n"
        "- 使用字符索引，起始索引 start_char_idx 含，结束索引 end_char_idx 不含（Python 切片风格）,注意结束索引的部分应该是需要符合句子的结束。\n"
        "- 索引基于我提供的原始文本 text，范围需满足：0 <= start_char_idx < end_char_idx <= len(text)。\n"
        "- 片段必须按原文顺序排列，严格连续、无重叠、无空洞：\n"
        "  - 第一个片段应满足 start_char_idx == 0；\n"
        "  - 相邻片段应满足 当前 end_char_idx == 下一个 start_char_idx；\n"
        "  - 最后一个片段应满足 end_char_idx == len(text)。\n"
        "- 所有索引按字符计数（基于 Python 的 len(text) 语义），不要按 token 或字节计数；\n"
        "  - 包括中英文、标点、空白、表情等，都按字符长度计算。\n"
        "- 索引必须是整数（不可为字符串/小数）。\n"
        "- 每个片段需给出简短、客观的 topic_description（不含表情/特殊符号）。\n"
        "- 输出的 JSON 结构只能包含：{\"topic_list\": [{\"topic_description\", \"start_char_idx\", \"end_char_idx\"}, ...]}。\n"
        "  - 严禁在每个片段内添加其他键（如 content）。\n"
        "- 仅输出 JSON，且不得包含任何额外文本、解释、Markdown 代码块标记或注释。\n\n"
        "示例（仅作格式参考）：\n"
    )

    prompt = (
        instructions
        + example_json
        + "\n\n原始文本如下（text）：\n<text>\n"
        + text
        + "\n</text>\n\n请直接输出 JSON（不包含任何额外说明或多余字段）。"
    )
    return prompt


def _strip_code_fences(text: str) -> str:
    """去除可能的 Markdown 代码块围栏，例如 ```json ... ``` 或 ``` ... ```。

    仅做最小且确定性的处理：
    - 若以三反引号开头，则去掉第一行（可能是 ``` 或 ```json），并在末尾去掉最后一行为 ``` 的围栏。
    - 同时去除首尾空白。
    """
    s = text.lstrip()
    if s.startswith("```"):
        # 切去首行围栏
        parts = s.splitlines()
        if parts:
            parts = parts[1:]
        # 若最后一行是 ```，去掉
        if parts and parts[-1].strip() == "```":
            parts = parts[:-1]
        s = "\n".join(parts)
    return s.strip()


def _parse_topic_list(resp_text: str) -> Dict[str, Any]:
    """直接解析 JSON。若解析失败，让异常抛出，便于及时暴露问题。"""
    cleaned = _strip_code_fences(resp_text)
    obj = json.loads(cleaned)
    # 只做最小校验：必须包含 topic_list
    if not isinstance(obj, dict) or "topic_list" not in obj:
        raise ValueError("模型输出缺少 topic_list")
    return obj


def _attach_content(text: str, topic_list: List[TopicSpan]) -> List[TopicSpanWithContent]:
    """根据起止索引从原文切片，拼接 content 字段。"""
    n = len(text)
    out: List[TopicSpanWithContent] = []
    for item in topic_list:
        s = int(item["start_char_idx"])  # 保守转换
        e = int(item["end_char_idx"])    # 保守转换
        if s < 0:
            s = 0
        if e > n:
            e = n
        if e <= s:
            continue
        out.append(
            {
                "topic_description": str(item["topic_description"]),
                "start_char_idx": s,
                "end_char_idx": e,
                "content": text[s:e],
            }
        )
    return out


def segment_text(text: str, *, model: Optional[str] = None) -> Dict[str, Any]:
    """将长文本交给大模型分块，并返回带 content 的主题列表。"""
    prompt = _build_prompt(text)
    resp_text = chat([{"role": "user", "content": prompt}], model=model)
    obj = _parse_topic_list(resp_text)
    topic_list: List[TopicSpan] = obj.get("topic_list", [])  # type: ignore
    topic_list_with_content = _attach_content(text, topic_list)
    return {"topic_list": topic_list_with_content}


def segment_text_to_file(
    text: str,
    out_json_path: str,
    *,
    model: Optional[str] = None,
) -> str:
    """分块并将结果写入 JSON 文件，返回保存路径。"""
    result = segment_text(text, model=model)
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return out_json_path


__all__ = [
    "TopicSpan",
    "TopicSpanWithContent",
    "segment_text",
    "segment_text_to_file",
]

