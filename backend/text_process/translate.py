# -*- coding: utf-8 -*-
"""
翻译模块：执行翻译、管理翻译结果。
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional

import tiktoken

from backend.chat_utils.chat_client import chat_text_async
from backend.schemas import Segment


def _split_segments_by_output_tokens(
    segments: List[Segment], max_tokens: int = 4096, encoding_name: str = "cl100k_base"
) -> List[List[Segment]]:
    """
    根据预估的翻译输出token数和句子数量，将分句分批。
    目标：每批约 10 句左右，但不超过 max_tokens 限制。

    参数:
    - segments: 要分批的分句列表
    - max_tokens: 每批最大输出token数（默认4096）
    - encoding_name: 编码方式

    返回: 分批后的分句列表
    """
    if not segments:
        return []

    # 目标：每批约 10 句
    target_batch_size = 10

    # 先按数量分批，然后检查 token 限制
    batches = []
    for i in range(0, len(segments), target_batch_size):
        batch = segments[i : i + target_batch_size]
        batches.append(batch)

    # 如果某个批次过大（token 超限），则进一步拆分
    enc = tiktoken.get_encoding(encoding_name)
    final_batches = []

    for batch in batches:
        # 估算这个批次的总 token 数
        total_tokens = 0
        for seg in batch:
            sentence = seg.get("sentence", "")
            estimated_tokens = int(len(enc.encode(sentence)) * 1.5) + 20
            total_tokens += estimated_tokens

        # 如果在 token 限制内，直接使用
        if total_tokens <= max_tokens:
            final_batches.append(batch)
        else:
            # 否则进一步拆分为更小的批次
            logging.warning(
                f"批次 token 数 ({total_tokens}) 超过限制 ({max_tokens})，"
                f"将 {len(batch)} 句拆分为更小的批次"
            )
            current_sub_batch = []
            current_tokens = 0

            for seg in batch:
                sentence = seg.get("sentence", "")
                estimated_tokens = int(len(enc.encode(sentence)) * 1.5) + 20

                if current_tokens + estimated_tokens > max_tokens and current_sub_batch:
                    final_batches.append(current_sub_batch)
                    current_sub_batch = [seg]
                    current_tokens = estimated_tokens
                else:
                    current_sub_batch.append(seg)
                    current_tokens += estimated_tokens

            if current_sub_batch:
                final_batches.append(current_sub_batch)

    return final_batches


def _build_translate_prompt(
    segments: List[Segment],
    source_lang: str,
    target_lang: str,
    all_segments: Optional[List[Segment]] = None,
) -> str:
    """
    构建翻译提示词，支持任意语言对，包含上下文信息。

    参数:
    - segments: 本批次要翻译的分句列表（约 10 句）
    - source_lang: 源语言名称（如 "English", "Chinese", "Japanese"）
    - target_lang: 目标语言名称
    - all_segments: 完整的分句列表（用于提供上下文，仅供参考）
    """
    header = f"""你是一个专业的{source_lang}至{target_lang}翻译专家。

翻译要求：
1. 准确传达原文含义，不要改变、扩展或删减原文内容
2. 保持原文的风格、语气和情感色彩
3. 保留专业术语和专有名词（如人名、地名、技术术语等）
4. 使用目标语言最自然的表达方式，避免生硬翻译
5. 不同语言的翻译长度可能差异很大，这是完全正常的（例如英文"Hello"可能翻译为中文"你好"）

关键要求 - 索引对应规则（必须严格遵守）：
- 【重要】每个翻译结果的 index 必须与【待翻译句子】中的 index 完全相同
- 【重要】每句话都有唯一的 index 标识符，返回的翻译必须一一对应
- 【重要】绝不能漏掉任何一句，绝不能改变顺序，绝不能重复
- 【重要】如果你注意到 index 不是连续的（如 0, 1, 3, 5），这是正常的，保持原样即可

工作流程：
1. 首先阅读【前文上下文】和【后文上下文】以了解语境（但这些内容本身不需要翻译）
2. 然后专注于翻译【待翻译句子】中的所有句子（只翻译这一部分）
3. 逐一确认每个句子都有唯一的翻译结果，index 必须完全对应

返回要求：
- 返回结果必须严格包含 START_TRANSLATIONS 和 END_TRANSLATIONS 边界标记
- 边界标记之间只能包含纯JSON数组格式
- JSON 数组必须包含所有待翻译句子的翻译结果（一个都不能少）
- 每个待翻译句子都必须有一个翻译条目，格式必须是（注意是单个大括号）: {"index": N, "translation": "翻译内容"}
- 严禁混入前文上下文或后文上下文的内容
- 禁止使用Markdown、代码块（```）、加粗、列表、编号等特殊格式

格式示例1（注意：假设待翻译句子的 index 是 0, 1, 2）：

START_TRANSLATIONS
[
  {"index": 0, "translation": "翻译后的句子0"},
  {"index": 1, "translation": "翻译后的句子1"},
  {"index": 2, "translation": "翻译后的句子2"}
]
END_TRANSLATIONS

格式示例2（假设输入 index 是 5, 7, 9）：

START_TRANSLATIONS
[
  {"index": 5, "translation": "翻译后的句子"},
  {"index": 7, "translation": "翻译后的句子"},
  {"index": 9, "translation": "翻译后的句子"}
]
END_TRANSLATIONS
""".strip()

    # 构建上下文部分
    context_lines = [header, ""]

    if all_segments is None:
        all_segments = segments

    # 获取第一个和最后一个要翻译句子的索引
    first_idx = segments[0].get("index", 0) if segments else 0
    last_idx = segments[-1].get("index", 0) if segments else 0

    # 添加前文上下文（前两句，如果存在）
    if first_idx > 0:
        context_lines.append("【前文上下文（仅供参考）】")
        prev_segments = []
        for seg in all_segments:
            seg_idx = seg.get("index", 0)
            if seg_idx < first_idx:
                prev_segments.append((seg_idx, seg))

        if prev_segments:
            for seg_idx, seg in prev_segments[-2:]:
                context_lines.append(f"{seg_idx}: {seg.get('sentence', '').strip()}")
            context_lines.append("")

    # 添加待翻译句子（这是唯一需要翻译的部分）
    context_lines.append("【待翻译句子】（必须逐一翻译，index必须一一对应）")
    for seg in segments:
        index = seg.get("index", 0)
        sentence = seg.get("sentence", "").strip()
        if sentence:
            context_lines.append(f"{index}: {sentence}")
    context_lines.append("")
    context_lines.append(
        f"（共 {len(segments)} 个句子需要翻译，检查：是否一个都没漏，是否顺序没乱，是否 index 完全对应）"
    )

    # 添加后文上下文（后两句，如果存在）
    max_idx = max((seg.get("index", 0) for seg in all_segments), default=0)
    if last_idx < max_idx:
        context_lines.append("【后文上下文（仅供参考）】")
        next_segments = []
        for seg in all_segments:
            seg_idx = seg.get("index", 0)
            if seg_idx > last_idx:
                next_segments.append((seg_idx, seg))

        if next_segments:
            for seg_idx, seg in next_segments[:2]:
                context_lines.append(f"{seg_idx}: {seg.get('sentence', '').strip()}")
            context_lines.append("")

    return "\n".join(context_lines)


def _extract_translations(response_text: str) -> Dict[int, str]:
    """
    从LLM响应中提取翻译结果，支持以下格式：
    1. START_TRANSLATIONS 和 END_TRANSLATIONS 边界标记
    2. translation_content: 标志 + ```json markdown 格式（向后兼容）
    3. 直接的 ```json markdown 格式（向后兼容）
    4. 纯 JSON 数组（向后兼容）

    返回一个字典，key 为 index，value 为翻译文本。
    """
    translations = {}

    try:
        cleaned = response_text.strip()

        # 首先尝试提取 START_TRANSLATIONS 到 END_TRANSLATIONS 之间的内容
        if "START_TRANSLATIONS" in cleaned and "END_TRANSLATIONS" in cleaned:
            start_idx = cleaned.find("START_TRANSLATIONS") + len("START_TRANSLATIONS")
            end_idx = cleaned.find("END_TRANSLATIONS")
            block = cleaned[start_idx:end_idx].strip()

            if block:
                # 直接解析JSON数组
                data = json.loads(block)
                if isinstance(data, list):
                    for item in data:
                        if (
                            isinstance(item, dict)
                            and "index" in item
                            and "translation" in item
                        ):
                            trans = item["translation"]
                            if isinstance(trans, str) and trans.strip():
                                translations[item["index"]] = trans.strip()
                return translations

        # 向后兼容：尝试提取 translation_content: 后的内容
        if "translation_content:" in cleaned:
            translation_start = cleaned.find("translation_content:")
            cleaned = cleaned[translation_start + len("translation_content:") :].strip()

        # 移除 markdown 代码块标记（如果有）
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        # 清理前后的空白符
        cleaned = cleaned.strip()

        # 尝试从回答中提取 JSON 数组
        # 处理 LLM 可能在 JSON 前后添加的说明文字
        if not cleaned.startswith("["):
            bracket_pos = cleaned.find("[")
            if bracket_pos >= 0:
                cleaned = cleaned[bracket_pos:]

        if not cleaned.endswith("]"):
            bracket_pos = cleaned.rfind("]")
            if bracket_pos >= 0:
                cleaned = cleaned[: bracket_pos + 1]

        # 如果仍然没有找到 JSON，尝试更激进的清理
        if not cleaned.startswith("[") or not cleaned.endswith("]"):
            logging.warning(f"无法识别JSON数组边界，原始响应: {response_text[:300]}")
            return translations

        # 解析 JSON，允许更多错误
        data = json.loads(cleaned)

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "index" in item and "translation" in item:
                    trans = item["translation"]
                    if isinstance(trans, str) and trans.strip():
                        translations[item["index"]] = trans.strip()
    except (json.JSONDecodeError, IndexError, KeyError, ValueError) as e:
        logging.warning(f"翻译结果解析失败: {e}，原始响应: {response_text[:300]}")

    # 诊断日志：检查 index 的顺序是否一致
    if translations:
        sorted_indices = sorted(translations.keys())
        logging.debug(f"提取的翻译 indices（顺序）: {sorted_indices}")

    return translations


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

                response = await chat_text_async(
                    prompt=retry_prompt,
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    max_tokens=2048,
                    timeout=60,
                    stream=True,
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
