"""转写记录服务层"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict

from backend.db.transcript_crud import (delete_transcript, get_summaries,
                                        get_transcript_by_id, get_translations)
from backend.db.transcript_query import (count_transcripts,
                                         list_transcripts_meta)
from backend.services.knowledge_base_service import knowledge_base


async def get_transcript_metadata_async(db_url: str, transcript_id: int) -> Dict[str, Any]:
    """获取转写记录的基本元数据（用于知识库）"""
    data = await asyncio.to_thread(get_transcript_by_id, db_url, transcript_id)
    if not data:
        return None

    # 只返回基本元数据，不包含大数据字段
    metadata = {
        "transcript_id": data.get("id"),
        "audio_path": data.get("audio_path"),
        "video_path": data.get("video_path"),
        "media_type": data.get("media_type"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "has_summary": bool(data.get("summaries_json")),
        "has_translation": bool(data.get("translations_json")),
        "has_chat_messages": bool(data.get("chat_messages_json"))
    }
    return metadata


async def list_transcripts_async(
    db_url: str, limit: int = 50, offset: int = 0
) -> Dict[str, Any]:
    """列出转写记录"""
    total = await asyncio.to_thread(count_transcripts, db_url)
    items = await asyncio.to_thread(
        list_transcripts_meta, db_url, limit=limit, offset=offset
    )
    return {"total": total, "items": items}


async def get_transcript_async(db_url: str, transcript_id: int) -> Dict[str, Any]:
    """获取转写记录详情及已保存的总结和翻译"""
    data = await asyncio.to_thread(get_transcript_by_id, db_url, transcript_id)

    if data:
        # 获取已保存的总结
        summaries = await asyncio.to_thread(get_summaries, db_url, transcript_id)
        # 获取已保存的翻译
        translations = await asyncio.to_thread(get_translations, db_url, transcript_id)

        data["summaries"] = summaries
        data["translations"] = translations

    return data


async def delete_transcript_async(
    db_url: str, transcript_id: int, static_dir: Path
) -> Dict[str, Any]:
    """删除转写记录及对应的视频文件"""
    logging.info(f"开始删除操作 - transcript_id: {transcript_id}")

    # 检查转写记录是否存在
    transcript = await asyncio.to_thread(get_transcript_by_id, db_url, transcript_id)
    if not transcript:
        logging.error(f"转写记录不存在: {transcript_id}")
        return None

    logging.info(f"找到转写记录: {transcript}")

    deleted_files = []
    errors = []

    try:
        # 第一步：删除视频文件
        media_path = transcript.get("media_path")
        if media_path:
            try:
                # 解析文件路径
                file_path = Path(media_path)

                # 安全检查：确保文件在静态目录内，防止路径遍历攻击
                try:
                    file_path.resolve().relative_to(static_dir.resolve())
                except ValueError:
                    # 如果文件不在静态目录内，尝试通过文件名在静态目录中查找
                    basename = file_path.name
                    file_path = static_dir / basename

                # 检查文件是否存在并删除
                if file_path.exists() and file_path.is_file():
                    file_path.unlink()  # 删除文件
                    deleted_files.append(str(file_path))
                    logging.info(f"已删除视频文件: {file_path}")
                else:
                    logging.warning(f"视频文件不存在: {file_path}")

            except Exception as e:
                error_msg = f"删除视频文件失败: {str(e)}"
                errors.append(error_msg)
                logging.error(error_msg)

        # 第二步：删除转写记录
        logging.info(f"开始删除数据库记录: {transcript_id}")
        success = await asyncio.to_thread(delete_transcript, db_url, transcript_id)
        logging.info(f"数据库删除结果: {success}")

        if not success:
            logging.error(f"数据库删除失败: {transcript_id}")
            return None

        logging.info(f"已删除转写记录: {transcript_id}")

        # 第三步：删除向量数据库中的相关向量
        try:
            # 使用条件删除：直接按 transcript_id 删除所有相关向量（高效推荐方式）
            knowledge_base.collection.delete(where={"transcript_id": transcript_id})
            logging.info(f"已删除向量数据库中 transcript_id={transcript_id} 的所有向量块")
        except Exception as e:
            error_msg = f"删除向量数据库失败: {str(e)}"
            errors.append(error_msg)
            logging.error(error_msg)

        # 返回结果
        message_parts = []
        if deleted_files:
            message_parts.append(f"已删除 {len(deleted_files)} 个视频文件")
        message_parts.append("转写记录删除成功")

        if errors:
            message_parts.append(f"但有 {len(errors)} 个错误")

        return {
            "success": True,
            "message": "，".join(message_parts),
            "transcript_id": transcript_id,
            "deleted_files": deleted_files,
            "errors": errors if errors else None,
        }
    except Exception as e:
        logging.error(f"删除操作失败: {e}")
        return None
