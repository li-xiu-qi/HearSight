"""
长文本主题分块（由大模型决定边界）。

用法：
- 调用 segment_text_to_file(text, out_json_path, model=None)；
- 输出格式：topic_segments: list(dict(topic, abstract))（不再返回字符索引与全文 content）。

注意：
- 本模块不使用本地 token 拆分；
- 索引基于传入的原始 text（字符级）；
- 仅做必要的校验与处理，保持最小实现。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict
import json

from backend.chat_utils.chat_client import chat


class TopicSegment(TypedDict):
    """主题片段（新输出结构）。"""
    topic: str          # 主题名/标题（简明）
    abstract: str       # 2-4 句更完整的摘要（概述这段在讲什么，包含关键点）


def _build_prompt(text: str) -> str:
    """构造提示词：让大模型对整段文本做主题分块并给出主题与简述。"""
    example_json = (
        '{\n'
        '  "topic_segments": [\n'
        '    {\n'
        '      "topic": "主题 A",\n'
        '      "abstract": "用 2-4 句完整阐述该段的主要内容与要点，保持客观描述，不要夸饰。"\n'
        '    },\n'
        '    {\n'
        '      "topic": "主题 B",\n'
        '      "abstract": "用 2-4 句完整阐述该段的主要内容与要点，保持客观描述，不要夸饰。"\n'
        '    }\n'
        '  ]\n'
        '}'
    )

    instructions = (
        "你将收到一段较长文本，请按语义将其分成若干主题片段，并返回每个片段的主题与简述。\n"
        "要求：\n"
        "- 按原文语义自然分段，保持顺序；不要输出与文本无关的主题。\n"
        "- 每个片段：\n"
        "  - topic：简明的主题标题；\n"
        "  - abstract：2-4 句更完整的摘要，覆盖关键观点/事实，保持客观与信息量。\n"
        "- 输出的 JSON 结构只能包含：{\"topic_segments\": [{\"topic\", \"abstract\"}, ...]}。\n"
        "  - 严禁包含其他键（如 content、start_char_idx、end_char_idx 等）。\n"
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


def _parse_topic_segments(resp_text: str) -> Dict[str, Any]:
    """直接解析 JSON。若解析失败，让异常抛出，便于及时暴露问题。"""
    cleaned = _strip_code_fences(resp_text)
    obj = json.loads(cleaned)
    # 只做最小校验：必须包含 topic_segments
    if not isinstance(obj, dict) or "topic_segments" not in obj:
        raise ValueError("模型输出缺少 topic_segments")
    return obj


def segment_text(text: str, *, model: Optional[str] = None) -> Dict[str, Any]:
    """将长文本交给大模型分块，返回 topic_segments: list(dict(topic, abstract))。"""
    prompt = _build_prompt(text)
    resp_text = chat([{"role": "user", "content": prompt}], model=model)
    obj = _parse_topic_segments(resp_text)
    segments: List[TopicSegment] = []
    for item in obj.get("topic_segments", []):  # type: ignore
        t = str(item.get("topic", "")).strip()
        a = str(item.get("abstract", "")).strip()
        if not t and not a:
            continue
        segments.append({"topic": t, "abstract": a})
    return {"topic_segments": segments}


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
    "TopicSegment",
    "segment_text",
    "segment_text_to_file",
]

