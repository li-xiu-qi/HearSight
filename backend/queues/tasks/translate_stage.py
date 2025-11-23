# -*- coding: utf-8 -*-
"""翻译任务处理阶段"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from backend.text_process.translate import translate_segments_async
from .progress_utils import update_task_progress, create_progress_info


def handle_translate_stage(
    segments: List[Dict],
    target_lang: str,
    source_lang: str,
    job_id: int,
    set_task_progress: Any,
    progress_redis_client: Any,
) -> Dict[str, Any]:
    """处理翻译任务阶段。

    Args:
        segments: 要翻译的分句列表
        target_lang: 目标语言代码
        source_lang: 源语言代码
        job_id: 任务ID
        set_task_progress: 进度更新函数
        progress_redis_client: Redis客户端

    Returns:
        翻译结果字典
    """
    logger = logging.getLogger(__name__)

    print(f"[DEBUG] handle_translate_stage 开始，job_id={job_id}, target_lang={target_lang}, segments_count={len(segments)}")

    try:
        # 更新进度：开始翻译处理
        progress_info = create_progress_info(
            job_id, "in-progress", "translate", 10,
            message="正在启动翻译处理...",
        )
        update_task_progress(set_task_progress, progress_redis_client, job_id, progress_info)

        # 执行翻译
        import asyncio

        # 创建进度回调函数
        def progress_callback(current: int, total: int):
            progress_percent = int((current / total) * 80) + 10  # 10-90%
            progress_info = create_progress_info(
                job_id, "in-progress", "translate", progress_percent,
                message=f"正在翻译 {current}/{total} 个分句...",
            )
            update_task_progress(set_task_progress, progress_redis_client, job_id, progress_info)

        # 执行异步翻译
        result = asyncio.run(translate_segments_async(
            segments=segments,
            target_lang_code=target_lang,
            source_lang_code=source_lang,
            max_tokens=4096,
            progress_callback=progress_callback,
        ))

        # 更新进度：翻译完成
        progress_info = create_progress_info(
            job_id, "in-progress", "translate", 90,
            message="翻译完成，正在保存结果...",
        )
        update_task_progress(set_task_progress, progress_redis_client, job_id, progress_info)

        # 返回翻译结果
        return {
            "translations": result,
            "total_segments": len(segments),
            "translated_segments": len([s for s in result if s.get("translation")]),
        }

    except Exception as e:
        logger.error(f"翻译任务失败: {e}")
        raise