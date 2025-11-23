# -*- coding: utf-8 -*-
"""
翻译功能测试脚本：测试两步翻译的效果。
"""
import asyncio
import logging
import sys
import os
import time

# 添加backend路径
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if backend_dir not in os.sys.path:
    sys.path.insert(0, backend_dir)

from text_process.translate.core import translate_segments_async

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def test_translation_comparison():
    """
    测试两步翻译的效果（双语：英文到中文）。
    """
    # 测试句子（英文到中文）
    test_segments = [
        {
            'index': 0,
            'sentence': 'The rapid advancement of artificial intelligence has transformed various industries, from healthcare to finance.'
        },
        {
            'index': 1,
            'sentence': 'Machine learning algorithms can now process vast amounts of data to make predictions and decisions.'
        },
        {
            'index': 2,
            'sentence': 'However, the ethical implications of AI deployment remain a significant concern for policymakers worldwide.'
        }
    ]

    print("=== 两步翻译效果测试（英文→中文） ===\n")
    print("测试句子：")
    for seg in test_segments:
        print(f"{seg['index']}: {seg['sentence']}")
    print()

    # 测试两步翻译
    print("翻译结果（直译 + 意译）：")
    result = await translate_segments_async(
        test_segments.copy(),
        target_lang_code="zh",
        source_lang_code="en"
    )

    print("\n原文 vs 翻译对照：")
    for seg in result:
        original = seg['sentence']
        translation = seg.get('translation', {}).get('zh', '无翻译')
        print(f"原文: {original}")
        print(f"翻译: {translation}")
        print("-" * 60)


async def test_chinese_to_english():
    """
    测试中文到英文的两步翻译。
    """
    # 测试句子（中文到英文）
    test_segments = [
        {
            'index': 0,
            'sentence': '人工智能的快速发展已经改变了各个行业，从医疗保健到金融。'
        },
        {
            'index': 1,
            'sentence': '机器学习算法现在可以处理大量数据来进行预测和决策。'
        },
        {
            'index': 2,
            'sentence': '然而，人工智能部署的伦理含义仍然是全球政策制定者的重要关切。'
        }
    ]

    print("=== 两步翻译效果测试（中文→英文） ===\n")
    print("测试句子：")
    for seg in test_segments:
        print(f"{seg['index']}: {seg['sentence']}")
    print()

    # 测试两步翻译
    print("翻译结果（直译 + 意译）：")
    result = await translate_segments_async(
        test_segments.copy(),
        target_lang_code="en",
        source_lang_code="zh"
    )

    print("\n原文 vs 翻译对照：")
    for seg in result:
        original = seg['sentence']
        translation = seg.get('translation', {}).get('en', '无翻译')
        print(f"原文: {original}")
        print(f"翻译: {translation}")
        print("-" * 60)
    """
    测试翻译性能。
    """
    print("=== 性能测试 ===\n")

    # 准备更多测试数据
    test_sentences = [
        "Natural language processing enables computers to understand human language.",
        "Deep learning models require significant computational resources.",
        "The future of AI depends on responsible development and deployment.",
        "Data privacy concerns are growing as AI systems become more pervasive.",
        "Explainable AI aims to make machine learning decisions transparent."
    ]

    test_segments = [{'index': i, 'sentence': sent} for i, sent in enumerate(test_sentences)]

    # 测试翻译性能
    start_time = time.time()
    result = await translate_segments_async(
        test_segments.copy(),
        target_lang_code="zh"
    )
    translation_time = time.time() - start_time

    print(f"翻译耗时: {translation_time:.2f}秒")
    print(f"翻译句子数: {len(test_sentences)}")
    print(".2f")


async def main():
    """
    主测试函数。
    """
    try:
        await test_translation_comparison()
        print("-" * 50)
        await test_chinese_to_english()
    except Exception as e:
        logging.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
