# -*- coding: utf-8 -*-
"""
两步翻译模块：实现直译 + 意译的两步翻译法。
"""
import asyncio
import logging
from typing import Dict, List, Optional

from backend.startup import get_llm_router

# 动态导入配置
import os
try:
    from backend.startup import get_llm_router
    from backend.config import settings
    from backend.schemas import Segment
except ImportError:
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    if backend_dir not in os.sys.path:
        os.sys.path.insert(0, backend_dir)
    from backend.startup import get_llm_router
    from backend.config import settings
    from backend.schemas import Segment

from .parser import extract_translations
from .prompt import build_literal_translate_prompt, build_meaning_translate_prompt


class TwoStepTranslator:
    """
    两步翻译器：先直译，再意译。
    """

    def __init__(self):
        self.router = get_llm_router()

    async def translate_batch(
        self,
        segments: List[Segment],
        source_lang: str,
        target_lang: str,
        all_segments: Optional[List[Segment]] = None,
        max_tokens: int = 4096,
    ) -> Dict[int, str]:
        """
        对一批句子执行两步翻译。

        参数:
        - segments: 要翻译的分句列表
        - source_lang: 源语言名称
        - target_lang: 目标语言名称
        - all_segments: 完整分句列表（上下文）
        - max_tokens: 最大token数

        返回: {index: final_translation}
        """
        # 第一步：直译
        literal_translations = await self._literal_translate(
            segments, source_lang, target_lang, all_segments, max_tokens
        )

        if not literal_translations:
            logging.warning("直译失败，返回空结果")
            return {}

        # 第二步：意译
        final_translations = await self._meaning_translate(
            segments, literal_translations, source_lang, target_lang, all_segments, max_tokens
        )

        return final_translations

    async def _literal_translate(
        self,
        segments: List[Segment],
        source_lang: str,
        target_lang: str,
        all_segments: Optional[List[Segment]] = None,
        max_tokens: int = 4096,
    ) -> Dict[int, str]:
        """
        执行直译步骤。
        """
        prompt = build_literal_translate_prompt(segments, source_lang, target_lang, all_segments)

        try:
            response = await self.router.acompletion(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                timeout=120,
                stream=True,
                temperature=0.3,  # 直译使用较低温度确保准确性
            )

            response_text = ""
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content

            logging.info(f"直译完成，解析结果")
            translations = extract_translations(response_text)
            return translations

        except Exception as e:
            logging.error(f"直译失败: {e}")
            return {}

    async def _meaning_translate(
        self,
        segments: List[Segment],
        literal_translations: Dict[int, str],
        source_lang: str,
        target_lang: str,
        all_segments: Optional[List[Segment]] = None,
        max_tokens: int = 4096,
    ) -> Dict[int, str]:
        """
        执行意译步骤，基于直译结果优化表达。
        """
        prompt = build_meaning_translate_prompt(
            segments, literal_translations, source_lang, target_lang, all_segments
        )

        try:
            response = await self.router.acompletion(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                timeout=120,
                stream=True,
                temperature=0.6,  # 意译使用适中温度提升自然度
            )

            response_text = ""
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content

            logging.info(f"意译完成，解析结果")
            translations = extract_translations(response_text)
            return translations

        except Exception as e:
            logging.error(f"意译失败，使用直译结果: {e}")
            # 意译失败时返回直译结果
            return literal_translations