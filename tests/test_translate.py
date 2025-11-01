# -*- coding: utf-8 -*-
"""
翻译功能测试脚本
"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_translate_prompt():
    """测试翻译提示词生成"""
    print("=== 翻译提示词测试 ===\n")
    
    from backend.text_process.translate import _build_translate_prompt
    
    segments = [
        {"index": 0, "sentence": "Hello, this is the first sentence.", "start_time": 0.0, "end_time": 3.5},
        {"index": 1, "sentence": "This is the second sentence.", "start_time": 3.5, "end_time": 7.2},
    ]
    
    prompt = _build_translate_prompt(segments, target_language="zh")
    print("英->中翻译提示词:")
    print(prompt)
    print("\n" + "="*50 + "\n")
    
    prompt = _build_translate_prompt(segments, target_language="en")
    print("中->英翻译提示词:")
    print(prompt)


def test_extract_translations():
    """测试翻译结果提取"""
    print("=== 翻译结果提取测试 ===\n")
    
    from backend.text_process.translate import _extract_translations
    
    # 测试1：正确的JSON响应
    response_correct = '''```json
[
    {"index": 0, "translation": "你好，这是第一句话。"},
    {"index": 1, "translation": "这是第二句话。"}
]
```'''
    
    translations = _extract_translations(response_correct)
    print("正确JSON响应提取结果:")
    print(f"翻译结果: {translations}\n")
    
    # 测试2：错误的响应
    response_wrong = "抱歉，我无法翻译这些句子。"
    translations = _extract_translations(response_wrong)
    print("错误响应提取结果:")
    print(f"翻译结果: {translations}\n")


def test_translate_segments_mock():
    """测试翻译分句（模拟LLM调用）"""
    print("=== 分句翻译测试（模拟）===\n")
    
    # 模拟翻译函数
    def mock_translate_segments(segments, **kwargs):
        # 模拟翻译结果
        mock_translations = {
            0: "你好，这是第一句话。",
            1: "这是第二句话。",
        }
        
        result = []
        for seg in segments:
            new_seg = dict(seg)
            index = seg.get("index", 0)
            if index in mock_translations:
                new_seg["translation"] = mock_translations[index]
            else:
                new_seg["translation"] = None
            result.append(new_seg)
        
        return result
    
    segments = [
        {"index": 0, "sentence": "Hello, this is the first sentence.", "start_time": 0.0, "end_time": 3.5},
        {"index": 1, "sentence": "This is the second sentence.", "start_time": 3.5, "end_time": 7.2},
    ]
    
    translated = mock_translate_segments(segments)
    
    print("原始分句:")
    for seg in segments:
        print(f"  {seg['index']}: {seg['sentence']}")
    
    print("\n翻译后分句:")
    for seg in translated:
        print(f"  {seg['index']}: {seg['sentence']} -> {seg.get('translation', '无翻译')}")


if __name__ == "__main__":
    test_translate_prompt()
    print("\n" + "="*80 + "\n")
    test_extract_translations()
    print("\n" + "="*80 + "\n")
    test_translate_segments_mock()
