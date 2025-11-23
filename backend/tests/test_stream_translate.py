#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试流式翻译功能
"""
import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import asyncio
from config import settings
from backend.text_process.translate import translate_segments_async

async def main():
    # 测试数据
    segments = [
        {"index": 0, "sentence": "Hello, this is an English video.", "start_time": 0.0, "end_time": 3.5},
        {"index": 1, "sentence": "We will discuss important topics today.", "start_time": 3.5, "end_time": 7.2},
        {"index": 2, "sentence": "Let's start with the first point.", "start_time": 7.2, "end_time": 10.0},
    ]
    
    def progress_callback(translated_count: int, total: int):
        progress = (translated_count / total * 100) if total > 0 else 0
        print(f"进度: {translated_count}/{total} ({progress:.1f}%)")
    
    print("开始流式翻译测试...")
    print("=" * 60)
    
    result = await translate_segments_async(
        segments,
        target_language="zh",
        max_tokens=4096,
        source_lang_name="English",
        target_lang_name="Chinese",
        progress_callback=progress_callback,
    )
    
    print("=" * 60)
    print("\n翻译完成结果:")
    for seg in result:
        trans = seg.get("translation", {})
        zh_trans = trans.get("zh", "无翻译") if isinstance(trans, dict) else "无翻译"
        print(f"[{seg['index']}] {seg['sentence']}")
        print(f"    -> {zh_trans}")

if __name__ == "__main__":
    asyncio.run(main())
