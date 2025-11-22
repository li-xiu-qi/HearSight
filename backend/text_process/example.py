"""
text_process 模块使用示例

演示如何使用基于 LiteLLM 的文本处理功能：
- chat_with_segment: 基于视频字幕进行问答
- summarize_segments: 总结视频字幕内容
- translate_segments: 翻译视频字幕
"""

import asyncio
import os
import sys

# 动态导入配置和模块
try:
    from config import settings
    from schemas import Segment
    from text_process.chat_with_segment import chat_with_segments
    from text_process.summarize import summarize_segments
    from text_process.translate import translate_segments_async as translate_segments
except ImportError:
    # 如果模块找不到，尝试添加backend路径
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from config import settings
    from schemas import Segment
    from text_process.chat_with_segment import chat_with_segments
    from text_process.summarize import summarize_segments
    from text_process.translate import translate_segments_async as translate_segments


def example_chat_with_segments():
    """示例：基于字幕内容进行问答"""
    print("=== 字幕问答示例 ===")

    # 示例字幕数据
    segments = [
        Segment(
            index=0,
            sentence="人工智能正在改变我们的生活方式。",
            start_time=0.0,
            end_time=3.5
        ),
        Segment(
            index=1,
            sentence="从智能手机到自动驾驶汽车，AI技术无处不在。",
            start_time=3.5,
            end_time=8.2
        ),
        Segment(
            index=2,
            sentence="未来AI将帮助我们解决更多复杂问题。",
            start_time=8.2,
            end_time=12.0
        )
    ]

    # 从配置中获取API设置
    api_key = settings.llm_provider_api_key
    base_url = settings.llm_provider_base_url
    model = settings.llm_model

    if not api_key:
        print("错误: 未配置 LLM API key")
        return

    # 问题
    question = "人工智能对生活有哪些影响？"

    try:
        # 调用问答功能
        response = chat_with_segments(
            segments=segments,
            question=question,
            api_key=api_key,
            base_url=base_url,
            model=model
        )

        print(f"问题: {question}")
        print(f"回答: {response}")
        print("✅ 问答成功")

    except Exception as e:
        print(f"❌ 问答失败: {e}")


def example_summarize_segments():
    """示例：总结字幕内容"""
    print("\n=== 字幕总结示例 ===")

    # 示例字幕数据
    segments = [
        Segment(
            index=0,
            sentence="机器学习是人工智能的重要分支。",
            start_time=0.0,
            end_time=4.0
        ),
        Segment(
            index=1,
            sentence="它通过数据训练模型来做出预测。",
            start_time=4.0,
            end_time=8.0
        ),
        Segment(
            index=2,
            sentence="深度学习使用神经网络处理复杂问题。",
            start_time=8.0,
            end_time=12.0
        ),
        Segment(
            index=3,
            sentence="这些技术正在各行业得到广泛应用。",
            start_time=12.0,
            end_time=16.0
        )
    ]

    # 从配置中获取API设置
    api_key = settings.llm_provider_api_key
    base_url = settings.llm_provider_base_url
    model = settings.llm_model

    if not api_key:
        print("错误: 未配置 LLM API key")
        return

    try:
        # 调用总结功能
        summaries = summarize_segments(
            segments=segments,
            api_key=api_key,
            base_url=base_url,
            model=model,
            max_tokens=1000
        )

        print(f"总结结果数量: {len(summaries)}")
        for i, summary in enumerate(summaries):
            print(f"总结 {i+1}: {summary.get('summary', 'N/A')}")
        print("✅ 总结成功")

    except Exception as e:
        print(f"❌ 总结失败: {e}")


async def example_translate_segments():
    """示例：翻译字幕内容"""
    print("\n=== 字幕翻译示例 ===")

    # 示例字幕数据
    segments = [
        Segment(
            index=0,
            sentence="Hello, welcome to our AI presentation.",
            start_time=0.0,
            end_time=3.0
        ),
        Segment(
            index=1,
            sentence="Today we will discuss machine learning.",
            start_time=3.0,
            end_time=6.0
        ),
        Segment(
            index=2,
            sentence="This technology is changing the world.",
            start_time=6.0,
            end_time=9.0
        )
    ]

    # 从配置中获取API设置
    api_key = settings.llm_provider_api_key
    base_url = settings.llm_provider_base_url
    model = settings.llm_model

    if not api_key:
        print("错误: 未配置 LLM API key")
        return

    try:
        # 调用翻译功能
        translations = await translate_segments(
            segments=segments,
            api_key=api_key,
            base_url=base_url,
            model=model,
            target_lang_code="zh",
            source_lang_code="en",
            source_lang_display_name="English",
            target_lang_display_name="Chinese",
            max_tokens=1000
        )

        print(f"翻译结果数量: {len(translations)}")
        for i, translation in enumerate(translations):
            original = translation.get('original', 'N/A')
            translated = translation.get('translation', 'N/A')
            print(f"原文 {i+1}: {original}")
            print(f"译文 {i+1}: {translated}")
            print()
        print("✅ 翻译成功")

    except Exception as e:
        print(f"❌ 翻译失败: {e}")


def main():
    """主函数：运行所有示例"""
    print("text_process 模块 LiteLLM 调用示例")
    print("=" * 40)

    # 检查配置
    if not settings.llm_provider_api_key:
        print("❌ 请先配置 LLM_PROVIDER_API_KEY 环境变量")
        return

    # 运行同步示例
    example_chat_with_segments()
    example_summarize_segments()

    # 运行异步示例
    asyncio.run(example_translate_segments())

    print("\n🎉 所有示例运行完成！")


if __name__ == "__main__":
    main()
