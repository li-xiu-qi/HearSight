"""翻译服务层"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, Optional

from backend.db.pg_store import update_transcript
from backend.text_process.translate import translate_segments_async

translate_tasks: Dict[int, Dict[str, Any]] = {}


async def start_translate_task(
    transcript_id: int,
    segments: list,
    target_language: str,
    max_tokens: int,
    api_key: str,
    base_url: str,
    model: str,
    source_lang_name: str,
    target_lang_name: str,
    db_url: str,
    force_retranslate: bool = False,
) -> Dict[str, Any]:
    """启动翻译任务"""
    logging.info(
        f"翻译请求开始 - transcript_id: {transcript_id}, target_language: {target_language}"
    )

    # 初始化任务状态
    translate_tasks[transcript_id] = {
        "status": "translating",
        "progress": 0,
        "translated_count": 0,
        "total_count": len(segments),
        "target_language": target_language,
        "message": "翻译中...",
    }

    # 启动后台翻译任务
    asyncio.create_task(
        _background_translate(
            transcript_id,
            segments,
            target_language,
            max_tokens,
            api_key,
            base_url,
            model,
            source_lang_name,
            target_lang_name,
            db_url,
            force_retranslate,
        )
    )

    return {
        "status": "started",
        "transcript_id": transcript_id,
        "total_count": len(segments),
    }


async def _background_translate(
    transcript_id: int,
    segments: list,
    target_language: str,
    max_tokens: int,
    api_key: str,
    base_url: str,
    model: str,
    source_lang_name: str,
    target_lang_name: str,
    db_url: str,
    force_retranslate: bool = False,
):
    """后台翻译任务"""
    try:
        total_count = len(segments)

        def progress_callback(translated_count: int, total: int):
            """更新翻译进度"""
            progress = (translated_count / total * 100) if total > 0 else 0
            translate_tasks[transcript_id] = {
                "status": "translating",
                "progress": progress,
                "translated_count": translated_count,
                "total_count": total_count,
                "target_language": target_language,
                "message": f"翻译进度：{translated_count}/{total_count}",
            }
            logging.info(
                f"翻译进度 - {translated_count}/{total_count} ({progress:.1f}%)"
            )

        # 执行翻译
        logging.info(f"开始翻译 {total_count} 个分句")
        translated_segments = await translate_segments_async(
            segments,
            api_key=api_key,
            base_url=base_url,
            model=model,
            target_language=target_language,
            max_tokens=max_tokens,
            source_lang_name=source_lang_name,
            target_lang_name=target_lang_name,
            progress_callback=progress_callback,
            force_retranslate=force_retranslate,
        )
        logging.info(f"翻译完成，开始保存到数据库")

        # 保存到数据库
        logging.info(f"保存翻译结果到数据库")
        success = await asyncio.to_thread(
            update_transcript, db_url, transcript_id, translated_segments
        )
        logging.info(f"数据库保存结果: success={success}")

        if success:
            translated_count = sum(
                1
                for seg in translated_segments
                if target_language in (seg.get("translation") or {})
            )
            logging.info(f"最终统计: {translated_count}/{total_count} 个分句已翻译")
            translate_tasks[transcript_id] = {
                "status": "completed",
                "progress": 100,
                "translated_count": translated_count,
                "total_count": total_count,
                "target_language": target_language,
                "message": f"翻译完成：{translated_count}/{total_count}",
            }
            logging.info(f"翻译完成 - {translated_count}/{total_count}")
        else:
            translate_tasks[transcript_id] = {
                "status": "error",
                "progress": 0,
                "translated_count": 0,
                "total_count": total_count,
                "target_language": target_language,
                "message": "保存到数据库失败",
            }
            logging.error(f"保存翻译结果失败")

    except Exception as e:
        logging.error(f"翻译出错: {e}")
        translate_tasks[transcript_id] = {
            "status": "error",
            "progress": 0,
            "translated_count": 0,
            "total_count": len(segments),
            "target_language": target_language,
            "message": str(e),
        }


def get_translate_progress(transcript_id: int) -> Dict[str, Any]:
    """获取翻译进度"""
    if transcript_id not in translate_tasks:
        return {
            "status": "idle",
            "progress": 0,
            "translated_count": 0,
            "total_count": 0,
            "message": "未进行翻译",
        }

    return translate_tasks[transcript_id]
