# -*- coding: utf-8 -*-
"""
测试新的翻译格式：translation_content: 标志和 ```json markdown 包装
"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_extract_translations():
    """测试翻译结果提取"""
    print("=== 翻译结果提取测试 ===\n")
    
    from backend.text_process.translate import _extract_translations
    
    # 测试1：新格式 - translation_content: + ```json markdown
    response_new_format = """
我来帮助您翻译这些句子。

translation_content:
```json
[
    {"index": 0, "translation": "你好，这是第一句话。"},
    {"index": 1, "translation": "这是第二句话。"},
    {"index": 2, "translation": "第三句翻译。"}
]
```

希望这些翻译满足您的需求。
"""
    
    translations = _extract_translations(response_new_format)
    print("新格式响应提取结果:")
    print(f"翻译结果: {translations}")
    print(f"提取数量: {len(translations)}\n")
    
    # 测试2：旧格式 - 直接 markdown JSON
    response_old_format = """```json
[
    {"index": 0, "translation": "你好"},
    {"index": 1, "translation": "世界"}
]
```"""
    
    translations = _extract_translations(response_old_format)
    print("旧格式响应提取结果:")
    print(f"翻译结果: {translations}")
    print(f"提取数量: {len(translations)}\n")
    
    # 测试3：最简格式 - 纯 JSON 数组
    response_pure_json = """[
    {"index": 0, "translation": "简单翻译"}
]"""
    
    translations = _extract_translations(response_pure_json)
    print("纯JSON格式响应提取结果:")
    print(f"翻译结果: {translations}")
    print(f"提取数量: {len(translations)}\n")
    
    # 测试4：带额外说明文字的新格式
    response_with_notes = """我来帮您翻译这些内容：

translation_content:
```json
[{"index": 0, "translation": "翻译好了"}]
```

已完成翻译工作。"""
    
    translations = _extract_translations(response_with_notes)
    print("带说明的新格式响应提取结果:")
    print(f"翻译结果: {translations}")
    print(f"提取数量: {len(translations)}\n")


def test_build_translate_prompt():
    """测试翻译提示词生成"""
    print("=== 翻译提示词生成测试 ===\n")
    
    from backend.text_process.translate import _build_translate_prompt
    
    segments = [
        {"index": 0, "sentence": "Hello, this is the first sentence.", "start_time": 0.0, "end_time": 3.5},
        {"index": 1, "sentence": "This is the second sentence.", "start_time": 3.5, "end_time": 7.2},
        {"index": 2, "sentence": "And the third one.", "start_time": 7.2, "end_time": 10.0},
    ]
    
    prompt = _build_translate_prompt(segments, source_lang="English", target_lang="Chinese")
    print("生成的翻译提示词:")
    print(prompt)
    print("\n" + "="*80 + "\n")
    
    # 检查是否包含关键信息
    if "translation_content:" in prompt:
        print("✓ 包含 translation_content: 标志")
    else:
        print("✗ 缺少 translation_content: 标志")
    
    if "```json" in prompt:
        print("✓ 包含 ```json markdown 格式指示")
    else:
        print("✗ 缺少 ```json markdown 格式指示")


def test_force_retranslate_logic():
    """测试强制重新翻译逻辑"""
    print("\n=== 强制重新翻译逻辑测试 ===\n")
    
    # 模拟原始分句（有些已翻译）
    segments = [
        {
            "index": 0,
            "sentence": "Hello",
            "translation": {"zh": "你好", "en": "Hello"}
        },
        {
            "index": 1,
            "sentence": "World",
            "translation": {"zh": "世界"}
        },
        {
            "index": 2,
            "sentence": "Test",
            "translation": None
        },
    ]
    
    target_language = "zh"
    
    # 情况1：正常翻译（只翻译未翻译的）
    print("情况1：正常翻译模式")
    untranslated = [
        seg for seg in segments
        if not seg.get("translation") or target_language not in (seg.get("translation") or {})
    ]
    print(f"原始分句数：{len(segments)}")
    print(f"需要翻译的分句数：{len(untranslated)}")
    print(f"需要翻译的索引：{[seg['index'] for seg in untranslated]}\n")
    
    # 情况2：强制重新翻译
    print("情况2：强制重新翻译模式")
    force_retranslate = True
    if force_retranslate:
        untranslated = segments
    print(f"原始分句数：{len(segments)}")
    print(f"需要翻译的分句数：{len(untranslated)}")
    print(f"需要翻译的索引：{[seg['index'] for seg in untranslated]}")


if __name__ == "__main__":
    test_extract_translations()
    test_build_translate_prompt()
    test_force_retranslate_logic()
