# -*- coding: utf-8 -*-
"""
翻译结果解析模块：解析翻译结果。
"""

from __future__ import annotations

import json
import logging
from typing import Dict, List


def _extract_translations(response_text: str) -> Dict[int, str]:
    """
    从LLM响应中提取翻译结果，支持以下格式：
    1. START_TRANSLATIONS 和 END_TRANSLATIONS 边界标记
    2. translation_content: 标志 + ```json markdown 格式（向后兼容）
    3. 直接的 ```json markdown 格式（向后兼容）
    4. 纯 JSON 数组（向后兼容）

    返回一个字典，key 为 index，value 为翻译文本。
    """
    translations = {}

    try:
        cleaned = response_text.strip()

        # 首先尝试提取 START_TRANSLATIONS 到 END_TRANSLATIONS 之间的内容
        if "START_TRANSLATIONS" in cleaned and "END_TRANSLATIONS" in cleaned:
            start_idx = cleaned.find("START_TRANSLATIONS") + len("START_TRANSLATIONS")
            end_idx = cleaned.find("END_TRANSLATIONS")
            block = cleaned[start_idx:end_idx].strip()

            if block:
                # 直接解析JSON数组
                data = json.loads(block)
                if isinstance(data, list):
                    for item in data:
                        if (
                            isinstance(item, dict)
                            and "index" in item
                            and "translation" in item
                        ):
                            trans = item["translation"]
                            if isinstance(trans, str) and trans.strip():
                                translations[item["index"]] = trans.strip()
                return translations

        # 向后兼容：尝试提取 translation_content: 后的内容
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

    # 诊断日志：检查 index 的顺序是否一致
    if translations:
        sorted_indices = sorted(translations.keys())
        logging.debug(f"提取的翻译 indices（顺序）: {sorted_indices}")

    return translations