"""翻译服务层"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

from backend.db.transcript_crud import (get_translations, save_translations,
                                        update_transcript)
from backend.text_process.translate import translate_segments_async

translate_tasks: Dict[int, Dict[str, Any]] = {}


async def start_translate_task(
    transcript_id: int,
    segments: list,
    target_lang_code: str,
    max_tokens: int,
    api_key: str,
    base_url: str,
    model: str,
    source_lang_code: str,
    source_lang_display_name: str,
    target_lang_display_name: str,
    db_url: str,
    force_retranslate: bool = False,
) -> Dict[str, Any]:
    """启动翻译任务"""
    logging.info(
        f"翻译请求开始 - transcript_id: {transcript_id}, target_lang_code: {target_lang_code}"
    )

    # 初始化任务状态
    translate_tasks[transcript_id] = {
        "status": "translating",
        "progress": 0,
        "translated_count": 0,
        "total_count": len(segments),
        "target_lang_code": target_lang_code,
        "message": "翻译中...",
    }

    # 启动后台翻译任务
    asyncio.create_task(
        _background_translate(
            transcript_id,
            segments,
            target_lang_code,
            max_tokens,
            api_key,
            base_url,
            model,
            source_lang_code,
            source_lang_display_name,
            target_lang_display_name,
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
    target_lang_code: str,
    max_tokens: int,
    api_key: str,
    base_url: str,
    model: str,
    source_lang_code: str,
    source_lang_display_name: str,
    target_lang_display_name: str,
    db_url: str,
    force_retranslate: bool = False,
):
    """后台翻译任务"""
    try:
        total_count = len(segments)

        def progress_callback(translated_count: int, total: int):
            """更新翻译进度"""
            progress = round(translated_count / total * 100) if total > 0 else 0
            translate_tasks[transcript_id] = {
                "status": "translating",
                "progress": progress,
                "translated_count": translated_count,
                "total_count": total_count,
                "target_lang_code": target_lang_code,
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
            target_lang_code=target_lang_code,
            source_lang_code=source_lang_code,
            max_tokens=max_tokens,
            source_lang_display_name=source_lang_display_name,
            target_lang_display_name=target_lang_display_name,
            progress_callback=progress_callback,
            force_retranslate=force_retranslate,
        )
        logging.info(f"翻译完成，开始保存到数据库")

        # 更新segments中的翻译内容
        logging.info(f"更新segments中的翻译内容")
        success_update_segments = await asyncio.to_thread(
            update_transcript, db_url, transcript_id, translated_segments
        )
        logging.info(f"Segments数据库保存结果: success={success_update_segments}")

        # 构建翻译结果对象并保存
        translations_dict = {target_lang_code: []}
        for seg in translated_segments:
            translation_data = seg.get("translation") or {}
            if target_lang_code in translation_data:
                translations_dict[target_lang_code].append(
                    {
                        "index": seg.get("index"),
                        "sentence": seg.get("sentence"),
                        "translation": translation_data[target_lang_code],
                        "start_time": seg.get("start_time"),
                        "end_time": seg.get("end_time"),
                    }
                )

        # 获取现有翻译（如果有）
        existing_translations = (
            await asyncio.to_thread(get_translations, db_url, transcript_id) or {}
        )

        # 合并翻译结果
        existing_translations[target_lang_code] = translations_dict[target_lang_code]

        # 保存到数据库
        logging.info(f"保存翻译结果到translations_json")
        success_save_trans = await asyncio.to_thread(
            save_translations, db_url, transcript_id, existing_translations
        )
        logging.info(f"翻译结果保存结果: success={success_save_trans}")

        if success_update_segments and success_save_trans:
            translated_count = len(translations_dict[target_lang_code])
            logging.info(f"最终统计: {translated_count}/{total_count} 个分句已翻译")
            translate_tasks[transcript_id] = {
                "status": "completed",
                "progress": 100,
                "translated_count": translated_count,
                "total_count": total_count,
                "target_lang_code": target_lang_code,
                "message": f"翻译完成：{translated_count}/{total_count}",
            }
            logging.info(f"翻译完成 - {translated_count}/{total_count}")
        else:
            translate_tasks[transcript_id] = {
                "status": "error",
                "progress": 0,
                "translated_count": 0,
                "total_count": total_count,
                "target_lang_code": target_lang_code,
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
            "target_lang_code": target_lang_code,
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
