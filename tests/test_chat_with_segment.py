#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from typing import List
from dotenv import load_dotenv  # 添加dotenv导入

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 从tests目录加载环境变量
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

from backend.text_process.chat_with_segment import _build_prompt
from backend.utils.typing_defs import Segment

def test_build_prompt():
    # 创建测试数据
    test_segments: List[Segment] = [
        {
            "index": 0,
            "sentence": "欢迎大家收看本期节目",
            "start_time": 0.0,
            "end_time": 3.5
        },
        {
            "index": 1,
            "sentence": "今天我们来讨论人工智能的发展趋势",
            "start_time": 3.5,
            "end_time": 8.2
        },
        {
            "index": 2,
            "sentence": "人工智能在医疗领域的应用越来越广泛",
            "start_time": 8.2,
            "end_time": 12.8
        }
    ]
    
    # 测试问题
    question = "人工智能在哪些领域有应用？"
    
    # 构建提示词
    prompt = _build_prompt(test_segments, question)
    
    # 打印提示词
    print("构建的提示词:")
    print(prompt)
    
    # 验证提示词包含关键元素
    assert "人工智能在哪些领域有应用？" in prompt
    assert "[0.00, 3.50] 欢迎大家收看本期节目" in prompt
    assert "输出格式示例" in prompt
    assert "[开始时间-结束时间]" in prompt
    
    print("\n提示词构建测试通过!")
    return True

if __name__ == "__main__":
    test_build_prompt()