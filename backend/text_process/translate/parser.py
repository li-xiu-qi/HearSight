# -*- coding: utf-8 -*-
"""
JSON 解析模块：从 LLM 响应中提取翻译结果。
"""
import json
import logging
from typing import Dict


def extract_translations(response_text: str) -> Dict[int, str]:
    """
    从 LLM 响应中提取翻译结果，支持以下格式：
    1. translation_content: 标志 + ```json markdown 格式
    2. 直接的 ```json markdown 格式
    3. 纯 JSON 数组

    参数:
    - response_text: LLM 的原始响应文本

    返回: 索引到翻译的字典 {index: translation}
    """
    translations = {}

    try:
        cleaned = response_text.strip()

        # 首先尝试提取 translation_content: 后的内容
        if "translation_content:" in cleaned:
            translation_start = cleaned.find("translation_content:")
            cleaned = cleaned[translation_start + len("translation_content:") :].strip()

        # 移除 markdown 代码块标记（如果有）
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        # 清理前后的空白符
        cleaned = cleaned.strip()

        # 尝试从回答中提取 JSON 数组
        # 处理 LLM 可能在 JSON 前后添加的说明文字
        if not cleaned.startswith("["):
            bracket_pos = cleaned.find("[")
            if bracket_pos >= 0:
                cleaned = cleaned[bracket_pos:]

        if not cleaned.endswith("]"):
            bracket_pos = cleaned.rfind("]")
            if bracket_pos >= 0:
                cleaned = cleaned[: bracket_pos + 1]

        # 如果仍然没有找到 JSON，尝试更激进的清理
        if not cleaned.startswith("[") or not cleaned.endswith("]"):
            logging.warning(f"无法识别JSON数组边界，原始响应: {response_text[:300]}")
            return translations

        # 解析 JSON，允许更多错误
        data = json.loads(cleaned)

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "index" in item and "translation" in item:
                    trans = item["translation"]
                    if isinstance(trans, str) and trans.strip():
                        translations[item["index"]] = trans.strip()
    except (json.JSONDecodeError, IndexError, KeyError, ValueError) as e:
        logging.warning(f"翻译结果解析失败: {e}，原始响应: {response_text[:300]}")

    return translations
