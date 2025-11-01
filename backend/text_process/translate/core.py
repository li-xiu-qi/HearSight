# -*- coding: utf-8 -*-
"""
核心翻译模块：主要的翻译流程控制和结果整合。
"""
import asyncio
import logging
from typing import Callable, Dict, List, Optional

from backend.chat_utils.chat_client import chat_text_async
from backend.utils.typing_defs import Segment

from .batch import split_segments_by_output_tokens
from .parser import extract_translations
from .prompt import build_translate_prompt


async def translate_segments_async(
    segments: List[Segment],
    api_key: str,
    base_url: str,
    model: str,
    target_language: str = "zh",
    max_tokens: int = 4096,
    source_lang_name: str = "",
    target_lang_name: str = "",
    progress_callback: Optional[Callable[[int, int], None]] = None,
    force_retranslate: bool = False,
) -> List[Segment]:
    """
    异步翻译分句。根据输出token限制自动分批处理。只翻译未翻译的分句。

    参数:
    - segments: 要翻译的分句列表
    - api_key: LLM API密钥
    - base_url: LLM API基础URL
    - model: 模型名
    - target_language: 目标语言代码 ("zh", "en", "ja" 等)
    - max_tokens: 每批翻译的最大输出token数（默认4096）
    - source_lang_name: 源语言名称（如 "English", "Chinese"）
    - target_lang_name: 目标语言名称
    - progress_callback: 进度回调函数，签名为 callback(translated_count, total_count)
    - force_retranslate: 是否强制重新翻译所有分句，默认 False

    返回: 包含翻译结果的分句列表
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
            or target_language not in (seg.get("translation") or {})
        ]

    logging.info(
        f"翻译分析: 总分句数={len(segments)}, 待翻译={len(untranslated_segments)}, 目标语言={target_language}, 强制重译={force_retranslate}"
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
    }

    # 使用提供的语言名称或默认映射
    source_name = source_lang_name or lang_names.get(
        target_language.replace("_to_", "_").split("_")[0], "原文"
    )
    target_name = target_lang_name or lang_names.get(
        target_language.split("_")[-1], target_language
    )

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
            response = await chat_text_async(
                prompt=prompt,
                api_key=api_key,
                base_url=base_url,
                model=model,
                max_tokens=max_tokens,
                timeout=120,
                stream=True,
            )
            logging.info(f"第 {batch_idx + 1} 批翻译成功，解析响应")
            logging.info(
                f"=== LLM 原始响应第 {batch_idx + 1} 批 ===\n{response}\n=== 响应结束 ==="
            )
        except Exception as e:
            logging.error(f"第 {batch_idx + 1} 批翻译失败: {e}")
            # 记录失败的索引，稍后处理
            for seg in batch:
                failed_indices.append(seg.get("index", 0))
            continue

        batch_translations = extract_translations(response)
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

                response = await chat_text_async(
                    prompt=retry_prompt,
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    max_tokens=2048,
                    timeout=60,
                    stream=True,
                )
                retry_trans = extract_translations(response)

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
            current_translation[target_language] = all_translations[index]
            new_seg["translation"] = current_translation
        # 如果已有翻译，保持不变
        result.append(new_seg)

    return result
