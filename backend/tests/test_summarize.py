# -*- coding: utf-8 -*-
"""
最小可运行示例：
- 构造少量句级段落（不含 spk_id），调用 summarize_once 并打印结果；
- 读取 config.yaml 中的 chat.{api_key, base_url, model} 作为调用所需配置；
- 若缺少必要配置，则直接打印提示并退出（不做 try/except）。

遵循项目约定：
- 交流与注释中文；
- 直接调用，避免 argparse/unittest；
- 最小测试原则。
"""
from __future__ import annotations

import json
import os
import sys
from typing import List, Dict, Any

# 兼容在 backend/tests 目录下直接运行：将项目根目录加入 sys.path
_THIS_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from backend.services.summarize_service import summarize_once  # noqa: E402


def run() -> None:
    # 构造最小段落列表
    segments: List[Dict[str, Any]] = [
        {"index": 1, "sentence": "你好，世界！这是一次最小总结测试。", "start_time": 0.0, "end_time": 1.2},
        {"index": 2, "sentence": "我们希望输出主题与简要总结。", "start_time": 1.2, "end_time": 2.8},
    ]

    # 执行一次总结
    items = summarize_once(segments)

    # 输出与保存
    print("summarize result:")
    print(json.dumps(items, ensure_ascii=False, indent=2))

    out_dir = os.path.join(_THIS_DIR, "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "summarize_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print("保存路径:", out_path)


if __name__ == "__main__":
    run()
