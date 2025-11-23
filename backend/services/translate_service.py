"""翻译服务层"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

from backend.db.transcript_crud import (get_translations, save_translations,
                                        update_transcript)
from backend.text_process.translate import translate_segments_async
from backend.startup import get_db_url
from backend.routers.progress_router import redis_client


async def start_translate_task(
    transcript_id: int,
    segments: list,
    target_lang_code: str,
    max_tokens: int,
    source_lang_code: str,
    source_lang_display_name: str,
    target_lang_display_name: str,
    force_retranslate: bool = False,
) -> Dict[str, Any]:
    """启动翻译任务"""
    logging.info(
        f"翻译请求开始 - transcript_id: {transcript_id}, target_lang_code: {target_lang_code}, force_retranslate: {force_retranslate}"
    )

    # 如果是强制重新翻译，清除之前的翻译结果
    if force_retranslate:
        db_url = get_db_url()
        try:
            # 清除数据库中的翻译结果
            existing_translations = (
                await asyncio.to_thread(get_translations, db_url, transcript_id) or {}
            )
            if target_lang_code in existing_translations:
                del existing_translations[target_lang_code]
                await asyncio.to_thread(save_translations, db_url, transcript_id, existing_translations)
                logging.info(f"清除之前的翻译结果: {target_lang_code}")
            
            # 清除segments中的翻译内容
            for seg in segments:
                if seg.get("translation") and target_lang_code in seg.get("translation", {}):
                    del seg["translation"][target_lang_code]
                    # 如果translation为空，删除整个字段
                    if not seg["translation"]:
                        del seg["translation"]
            
            # 更新数据库中的segments
            await asyncio.to_thread(update_transcript, db_url, transcript_id, segments)
            logging.info(f"清除segments中的翻译内容: {target_lang_code}")
        except Exception as e:
            logging.warning(f"清除之前的翻译结果失败: {e}")

    # 初始化任务状态到Redis（重置进度）
    task_data = {
        "status": "translating",
        "progress": 0,
        "translated_count": 0,
        "total_count": len(segments),
        "target_lang_code": target_lang_code,
        "message": "翻译中...",
    }
    redis_client.set(f"translate_task:{transcript_id}", json.dumps(task_data))

    # 启动后台翻译任务
    asyncio.create_task(
        _background_translate(
            transcript_id,
            segments,
            target_lang_code,
            max_tokens,
            source_lang_code,
            source_lang_display_name,
            target_lang_display_name,
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
    source_lang_code: str,
    source_lang_display_name: str,
    target_lang_display_name: str,
    force_retranslate: bool = False,
):
    """后台翻译任务"""
    db_url = get_db_url()
    try:
        total_count = len(segments)

        def progress_callback(translated_count: int, total: int):
            """更新翻译进度"""
            progress = round(translated_count / total * 100) if total > 0 else 0
            task_data = {
                "status": "translating",
                "progress": progress,
                "translated_count": translated_count,
                "total_count": total_count,
                "target_lang_code": target_lang_code,
                "message": f"翻译进度：{translated_count}/{total_count}",
            }
            redis_client.set(f"translate_task:{transcript_id}", json.dumps(task_data))
            logging.info(
                f"翻译进度 - {translated_count}/{total_count} ({progress:.1f}%)"
            )

        # 执行翻译
        logging.info(f"开始翻译 {total_count} 个分句")
        translated_segments = await translate_segments_async(
            segments,
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
            task_data = {
                "status": "completed",
                "progress": 100,
                "translated_count": translated_count,
                "total_count": total_count,
                "target_lang_code": target_lang_code,
                "message": f"翻译完成：{translated_count}/{total_count}",
            }
            redis_client.set(f"translate_task:{transcript_id}", json.dumps(task_data))
            logging.info(f"翻译完成 - {translated_count}/{total_count}")
        else:
            task_data = {
                "status": "error",
                "progress": 0,
                "translated_count": 0,
                "total_count": total_count,
                "target_lang_code": target_lang_code,
                "message": "保存到数据库失败",
            }
            redis_client.set(f"translate_task:{transcript_id}", json.dumps(task_data))
            logging.error(f"保存翻译结果失败")

    except Exception as e:
        logging.error(f"翻译出错: {e}")
        task_data = {
            "status": "error",
            "progress": 0,
            "translated_count": 0,
            "total_count": len(segments),
            "target_lang_code": target_lang_code,
            "message": str(e),
        }
        redis_client.set(f"translate_task:{transcript_id}", json.dumps(task_data))


def get_translate_progress(transcript_id: int) -> Dict[str, Any]:
    """获取翻译进度"""
    task_data_json = redis_client.get(f"translate_task:{transcript_id}")
    if not task_data_json:
        return {
            "status": "idle",
            "progress": 0,
            "translated_count": 0,
            "total_count": 0,
            "message": "未进行翻译",
        }

    try:
        return json.loads(task_data_json)
    except json.JSONDecodeError:
        return {
            "status": "error",
            "progress": 0,
            "translated_count": 0,
            "total_count": 0,
            "message": "进度数据格式错误",
        }
