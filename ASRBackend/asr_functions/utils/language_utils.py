"""语言检测工具模块"""

import unicodedata


def detect_language(text: str) -> str:
    """检测文本主要语言，支持中文和英文。

    如果中文字符比例 > 70%，返回 'zh'，否则返回 'en'。
    """
    if not text:
        return "en"

    chinese_count = 0
    total_count = 0
    for char in text:
        if char.isspace():
            continue
        total_count += 1
        if unicodedata.category(char).startswith("Lo") or "\u4e00" <= char <= "\u9fff":
            chinese_count += 1

    if total_count == 0:
        return "en"

    chinese_ratio = chinese_count / total_count
    return "zh" if chinese_ratio > 0.7 else "en"
