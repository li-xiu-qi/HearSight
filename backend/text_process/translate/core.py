# -*- coding: utf-8 -*-
"""
核心翻译模块：主要的翻译流程控制和结果整合。
"""
import asyncio
import logging
import os
from typing import Callable, Dict, List, Optional

# 动态导入配置
try:
    from backend.startup import get_llm_router
    from backend.config import settings
    from backend.schemas import Segment
except ImportError:
    # 如果backend模块找不到，尝试添加路径
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    if backend_dir not in os.sys.path:
        os.sys.path.insert(0, backend_dir)
    from backend.startup import get_llm_router
    from backend.config import settings
    from backend.schemas import Segment

from .batch import split_segments_by_output_tokens
from .two_step_translate import TwoStepTranslator


async def translate_segments_async(
    segments: List[Segment],
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
    使用两步翻译法（直译 + 意译）提升翻译质量。
    仅支持双语翻译：中文(zh)和英文(en)的双向互译。

    参数:
    - segments: 要翻译的分句列表
    - target_lang_code: 目标语言代码，仅支持"zh"(中文)和"en"(英文)
    - source_lang_code: 源语言代码，仅支持"en"(英文)和"zh"(中文)，为空时由LLM自动检测
    - max_tokens: 每批翻译的最大输出token数，默认4096
    - source_lang_display_name: 源语言的显示名称，如"English"、"中文"，为空时使用默认值"原文"
    - target_lang_display_name: 目标语言的显示名称，如"中文"、"English"，为空时根据target_lang_code自动推断
    - force_retranslate: 是否强制重新翻译所有分句（包括已翻译的），默认False

    返回: 包含翻译结果的分句列表，每个分句的translation字段会包含目标语言的翻译
    """
    if not segments:
        return segments

    # 验证语言支持（仅支持双语）
    supported_langs = {"zh", "en"}
    if target_lang_code not in supported_langs:
        raise ValueError(f"不支持的目标语言: {target_lang_code}。仅支持: {supported_langs}")
    if source_lang_code and source_lang_code not in supported_langs:
        raise ValueError(f"不支持的源语言: {source_lang_code}。仅支持: {supported_langs}")

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

    # 设置默认语言名称映射（仅支持双语：中文和英文）
    lang_names = {
        "zh": "中文",
        "en": "英文",
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
    translator = TwoStepTranslator()

    for batch_idx, batch in enumerate(batches):
        logging.info(f"翻译第 {batch_idx + 1}/{len(batches)} 批（{len(batch)} 个分句）")

        try:
            # 使用两步翻译法
            batch_translations = await translator.translate_batch(
                batch, source_name, target_name, segments, max_tokens
            )

        except Exception as e:
            logging.error(f"第 {batch_idx + 1} 批翻译失败: {e}")
            # 记录失败的索引，稍后处理
            for seg in batch:
                failed_indices.append(seg.get("index", 0))
            continue

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
                # 重试使用两步翻译法
                retry_trans = await translator.translate_batch(
                    retry_batch, source_name, target_name, segments, 2048
                )

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
