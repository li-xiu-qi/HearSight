# -*- coding: utf-8 -*-
"""
核心翻译模块：主要的翻译流程控制和结果整合。
"""
import asyncio
import logging
import os
from typing import Callable, Dict, List, Optional

import litellm

# 动态导入配置
try:
    from backend.config import settings
    from backend.schemas import Segment
except ImportError:
    # 如果backend模块找不到，尝试添加路径
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    if backend_dir not in os.sys.path:
        os.sys.path.insert(0, backend_dir)
    from backend.config import settings
    from backend.schemas import Segment

from .batch import split_segments_by_output_tokens
from .parser import extract_translations
from .prompt import build_translate_prompt


async def translate_segments_async(
    segments: List[Segment],
    api_key: str,
    base_url: str,
    model: str,
    target_lang_code: str = "zh",
    source_lang_code: str = "",
    max_tokens: int = 4096,
    source_lang_display_name: str = "",
    target_lang_display_name: str = "",
    progress_callback: Optional[Callable[[int, int], None]] = None,
    force_retranslate: bool = False,
) -> List[Segment]:
    """
    异步翻译分句。根据输出token限制自动分批处理。只翻译未翻译的分句。

    参数:
    - segments: 要翻译的分句列表
    - api_key: LLM API密钥，用于访问语言模型服务
    - base_url: LLM API基础URL，指定API服务器地址
    - model: 使用的语言模型名称
    - target_lang_code: 目标语言代码，如"zh"(中文)、"en"(英文)、"ja"(日文)等
    - source_lang_code: 源语言代码，如"en"(英文)、"zh"(中文)，为空时由LLM自动检测
    - max_tokens: 每批翻译的最大输出token数，默认4096
    - source_lang_display_name: 源语言的显示名称，如"English"、"中文"，为空时使用默认值"原文"
    - target_lang_display_name: 目标语言的显示名称，如"中文"、"English"，为空时根据target_lang_code自动推断
    - progress_callback: 翻译进度回调函数，参数为(translated_count, total_count)
    - force_retranslate: 是否强制重新翻译所有分句（包括已翻译的），默认False

    返回: 包含翻译结果的分句列表，每个分句的translation字段会包含目标语言的翻译
    """
    if not segments:
        return segments

    # 过滤出待翻译的分句
    if force_retranslate:
        # 强制重新翻译：所有分句都需要重新翻译
        untranslated_segments = segments
        logging.info(f"强制重新翻译模式启用，将重新翻译所有 {len(segments)} 个分句")
    else:
        # 正常模式：只翻译未翻译的分句（检查目标语言是否已有翻译）
        untranslated_segments = [
            seg
            for seg in segments
            if not seg.get("translation")
            or target_lang_code not in (seg.get("translation") or {})
        ]

    logging.info(
        f"翻译分析: 总分句数={len(segments)}, 待翻译={len(untranslated_segments)}, 目标语言={target_lang_code}, 强制重译={force_retranslate}"
    )

    if not untranslated_segments:
        # 所有都已翻译，直接返回
        logging.info("所有分句都已翻译，跳过翻译")
        if progress_callback:
            progress_callback(len(segments), len(segments))
        return segments

    # 设置默认语言名称映射
    lang_names = {
        "zh": "中文",
        "en": "英文",
        "ja": "日文",
        "ko": "韩文",
        "fr": "法文",
        "de": "德文",
        "es": "西班牙文",
        "it": "意大利文",
        "pt": "葡萄牙文",
        "ru": "俄文",
    }

    # 使用提供的语言名称或默认映射
    source_name = source_lang_display_name or lang_names.get(source_lang_code, "原文")  # 源语言名称
    target_name = target_lang_display_name or lang_names.get(target_lang_code, target_lang_code)  # 目标语言名称

    # 按输出token分批（只对未翻译的分句）
    batches = split_segments_by_output_tokens(untranslated_segments, max_tokens)
    logging.info(f"分成 {len(batches)} 批进行翻译")

    all_translations: Dict[int, str] = {}
    failed_indices: List[int] = []

    # 第一阶段：主翻译循环
    for batch_idx, batch in enumerate(batches):
        logging.info(f"翻译第 {batch_idx + 1}/{len(batches)} 批（{len(batch)} 个分句）")
        # 传递完整的 segments 作为上下文，帮助 LLM 理解语境
        prompt = build_translate_prompt(
            batch, source_name, target_name, all_segments=segments
        )

        # 打印提示词用于调试
        logging.info(
            f"=== 提示词第 {batch_idx + 1} 批 ===\n{prompt}\n=== 提示词结束 ==="
        )

        try:
            # 设置 LiteLLM 环境变量
            os.environ["OPENAI_API_KEY"] = api_key
            if base_url:
                os.environ["OPENAI_API_BASE"] = base_url

            response = await litellm.acompletion(
                model=f"openai/{model}",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                timeout=120,
                stream=True,
                temperature=0.6,
            )

            # 累积流式响应
            response_text = ""
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content

            logging.info(f"第 {batch_idx + 1} 批翻译成功，解析响应")
            logging.info(
                f"=== LLM 原始响应第 {batch_idx + 1} 批 ===\n{response_text}\n=== 响应结束 ==="
            )
        except Exception as e:
            logging.error(f"第 {batch_idx + 1} 批翻译失败: {e}")
            # 记录失败的索引，稍后处理
            for seg in batch:
                failed_indices.append(seg.get("index", 0))
            continue

        batch_translations = extract_translations(response_text)
        logging.info(
            f"第 {batch_idx + 1} 批解析出 {len(batch_translations)} 个翻译结果"
        )

        # 质量检查：验证翻译的有效性
        quality_checked = {}
        for seg in batch:
            index = seg.get("index", 0)
            if index in batch_translations:
                translated = batch_translations[index].strip()

                # 只检查翻译是否为空
                if len(translated) > 0:
                    quality_checked[index] = translated
                else:
                    logging.warning(f"翻译结果为空 (index={index})")
                    failed_indices.append(index)
            else:
                logging.warning(f"未获得翻译结果 (index={index})")
                failed_indices.append(index)

        all_translations.update(quality_checked)

        # 回调进度
        if progress_callback:
            translated_count = sum(
                1
                for seg in segments
                if seg.get("translation") or seg.get("index") in all_translations
            )
            if asyncio.iscoroutinefunction(progress_callback):
                await progress_callback(translated_count, len(segments))
            else:
                progress_callback(translated_count, len(segments))

        # 让出控制权，允许其他任务执行
        await asyncio.sleep(0)

    # 第二阶段：重试失败的翻译（分组重试，每组最多 5 个句子）
    if failed_indices:
        logging.warning(
            f"共有 {len(failed_indices)} 个分句翻译失败或质量不达标，尝试重试"
        )
        retry_segments = [
            seg for seg in untranslated_segments if seg.get("index") in failed_indices
        ]

        # 分组重试（每组最多 5 个失败的句子）
        retry_batch_size = 5
        for retry_batch_start in range(0, len(retry_segments), retry_batch_size):
            retry_batch = retry_segments[
                retry_batch_start : retry_batch_start + retry_batch_size
            ]
            retry_indices = [seg.get("index", 0) for seg in retry_batch]

            # 检查是否所有句子都已经翻译成功
            if all(idx in all_translations for idx in retry_indices):
                logging.info("重试批次已全部成功，跳过")
                continue

            try:
                retry_prompt = build_translate_prompt(
                    retry_batch, source_name, target_name, all_segments=segments
                )
                logging.info(
                    f"重试 {len(retry_batch)} 个失败的分句 (indices: {retry_indices})"
                )

                # 设置 LiteLLM 环境变量
                os.environ["OPENAI_API_KEY"] = api_key
                if base_url:
                    os.environ["OPENAI_API_BASE"] = base_url

                response = await litellm.acompletion(
                    model=f"openai/{model}",
                    messages=[{"role": "user", "content": retry_prompt}],
                    max_tokens=2048,
                    timeout=60,
                    stream=True,
                    temperature=0.6,
                )

                # 累积流式响应
                response_text = ""
                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        response_text += chunk.choices[0].delta.content

                retry_trans = extract_translations(response_text)

                # 统计重试成功的数量
                success_count = 0
                for idx in retry_indices:
                    if idx in retry_trans and idx not in all_translations:
                        all_translations[idx] = retry_trans[idx]
                        success_count += 1

                if success_count > 0:
                    logging.info(f"重试成功: {success_count}/{len(retry_batch)} 个分句")
                else:
                    logging.warning("重试未获得新的翻译结果")

            except Exception as e:
                logging.error(f"重试批次失败 (indices: {retry_indices}): {e}")

    # 第三阶段：更新结果，保留原有翻译
    result = []
    for seg in segments:
        new_seg = dict(seg)
        index = seg.get("index", 0)
        if index in all_translations:
            # 保存为字典格式，支持多语言
            current_translation = new_seg.get("translation") or {}
            if not isinstance(current_translation, dict):
                current_translation = {}
            current_translation[target_lang_code] = all_translations[index]
            new_seg["translation"] = current_translation
        # 如果已有翻译，保持不变
        result.append(new_seg)

    return result
