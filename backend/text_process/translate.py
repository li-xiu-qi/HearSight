# -*- coding: utf-8 -*-
"""
翻译模块：执行翻译、管理翻译结果。
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Callable, Dict, List, Optional
from backend.startup import get_llm_router

# 动态导入配置
try:
    from backend.config import settings
    from backend.schemas import Segment
except ImportError:
    # 如果backend模块找不到，尝试添加路径
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if backend_dir not in os.sys.path:
        os.sys.path.insert(0, backend_dir)
    from backend.config import settings
    from backend.schemas import Segment

from backend.utils.token_utils.calculate_tokens import OpenAITokenCalculator
from backend.text_process.translate_batch_service import _split_segments_by_output_tokens
from backend.text_process.translate_prompt_service import _build_translate_prompt
from backend.text_process.translate_result_service import _extract_translations


async def translate_segments_async(
    segments: List[Segment],
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
        logging.info(f"所有分句都已翻译，跳过翻译")
        if progress_callback:
            progress_callback(len(segments), len(segments))
        return segments

    # 设置默认语言名称映射
    lang_names = {
        "zh": "中文",
        "en": "英文",
        "ja": "日文",
        "ko": "韩文",
        "es": "西班牙文",
        "fr": "法文",
        "de": "德文",
        "ru": "俄文",
    }

    # 使用提供的语言名称或默认映射
    target_name = target_lang_name or lang_names.get(
        target_language.split("_")[-1], target_language
    )
    source_name = source_lang_name or "原文"

    # 按输出token分批（只对未翻译的分句）
    batches = _split_segments_by_output_tokens(untranslated_segments, max_tokens)
    logging.info(f"分成 {len(batches)} 批进行翻译")

    all_translations: Dict[int, str] = {}
    failed_indices: List[int] = []

    for batch_idx, batch in enumerate(batches):
        logging.info(f"翻译第 {batch_idx + 1}/{len(batches)} 批（{len(batch)} 个分句）")
        # 传递完整的 segments 作为上下文，帮助 LLM 理解语境
        prompt = _build_translate_prompt(
            batch, source_name, target_name, all_segments=segments
        )

        try:
            # 使用全局 LLM Router
            router = get_llm_router()

            # 使用 LiteLLM Router 异步调用
            response = await router.acompletion(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                timeout=120,
                stream=True,
                temperature=0.6,
            )
            logging.info(f"第 {batch_idx + 1} 批翻译成功，解析响应")
        except Exception as e:
            logging.error(f"第 {batch_idx + 1} 批翻译失败: {e}")
            # 记录失败的索引，稍后处理
            for seg in batch:
                failed_indices.append(seg.get("index", 0))
            continue

        batch_translations = _extract_translations(response)
        logging.info(
            f"第 {batch_idx + 1} 批解析出 {len(batch_translations)} 个翻译结果 (from {len(batch)} 个请求)"
        )

        if len(batch_translations) == 0:
            logging.warning(
                f"第 {batch_idx + 1} 批 LLM 未返回有效的翻译结果，可能的原因："
            )
            logging.warning(f"  - API 返回了非 JSON 格式的响应")
            logging.warning(f"  - 网络超时或错误")
            logging.warning(f"  - LLM 返回的错误消息而非翻译")
            for seg in batch:
                failed_indices.append(seg.get("index", 0))
            continue

        # 质量检查：验证翻译的有效性和完整性
        quality_checked = {}
        expected_indices = {seg.get("index", 0) for seg in batch}
        received_indices = set(batch_translations.keys())

        # 检查是否有漏掉的句子
        missing_indices = expected_indices - received_indices
        if missing_indices:
            logging.error(
                f"第 {batch_idx + 1} 批：LLM 漏掉了以下句子的翻译，indices: {sorted(missing_indices)}"
            )
            for idx in missing_indices:
                failed_indices.append(idx)

        # 检查是否有多余的翻译（可能是 LLM 误解了提示词）
        extra_indices = received_indices - expected_indices
        if extra_indices:
            logging.warning(
                f"第 {batch_idx + 1} 批：LLM 返回了额外的翻译，indices: {sorted(extra_indices)}（将被忽略）"
            )

        for seg in batch:
            index = seg.get("index", 0)
            if index in batch_translations:
                original = seg.get("sentence", "").strip()
                translated = batch_translations[index].strip()

                # 只检查翻译是否为空，不做长度检查
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
            translated_count = len(
                [
                    seg
                    for seg in untranslated_segments
                    if seg.get("index") in all_translations
                ]
            )
            if asyncio.iscoroutinefunction(progress_callback):
                await progress_callback(translated_count, len(untranslated_segments))
            else:
                progress_callback(translated_count, len(untranslated_segments))

        # 让出控制权，允许其他任务执行
        await asyncio.sleep(0)

    # 重试失败的翻译（分组重试，每组最多 5 个句子）
    if failed_indices:
        logging.warning(
            f"共有 {len(failed_indices)} 个分句翻译失败或未获得结果，索引为: {failed_indices[:10]}{'...' if len(failed_indices) > 10 else ''}"
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
                logging.info(f"重试批次 {retry_indices} 已全部成功，跳过")
                continue

            try:
                # 使用重试提示词，确保格式一致
                retry_prompt = _build_translate_prompt(
                    retry_batch, source_name, target_name, all_segments=segments
                )
                logging.info(
                    f"重试 {len(retry_batch)} 个失败的分句 (indices: {retry_indices})"
                )

                # 设置 LiteLLM 环境变量
                router = get_llm_router()

                response = await router.acompletion(
                    model=settings.llm_model,
                    messages=[{"role": "user", "content": retry_prompt}],
                    max_tokens=2048,
                    timeout=60,
                    stream=True,
                    temperature=0.6,
                )
                retry_trans = _extract_translations(response)

                # 统计重试成功的数量
                success_count = 0
                for idx in retry_indices:
                    if idx in retry_trans and idx not in all_translations:
                        all_translations[idx] = retry_trans[idx]
                        success_count += 1

                if success_count > 0:
                    logging.info(f"重试成功: {success_count}/{len(retry_batch)} 个分句")
                else:
                    logging.warning(f"重试未获得新的翻译结果，indices: {retry_indices}")

            except Exception as e:
                logging.error(f"重试批次失败 (indices: {retry_indices}): {e}")

    # 最终验证：检查是否有未翻译的句子
    still_failed = [
        seg.get("index", 0)
        for seg in untranslated_segments
        if seg.get("index", 0) not in all_translations
    ]

    if still_failed:
        logging.error(
            f"⚠️ 最终检查：仍有 {len(still_failed)} 个分句未能成功翻译，indices: {still_failed[:20]}{'...' if len(still_failed) > 20 else ''}"
        )
    else:
        logging.info(f"✅ 所有 {len(untranslated_segments)} 个待翻译分句都已成功翻译")

    # 更新结果，保留原有翻译
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
