# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
import logging

from backend.db.pg_store import (
    list_transcripts_meta,
    count_transcripts,
    get_transcript_by_id,
    delete_transcript,
)

router = APIRouter(prefix="/api", tags=["transcripts"])


@router.get("/transcripts")
def api_list_transcripts(request: Request, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """列出已转写的媒体列表（按id倒序）。
    Query:
      - limit: 返回数量（默认50）
      - offset: 偏移量（默认0）
    返回: { total, items: [{id, media_path, created_at, segment_count}] }
    """
    db_url = request.app.state.db_url
    total = count_transcripts(db_url)
    items = list_transcripts_meta(db_url, limit=limit, offset=offset)
    return {"total": total, "items": items}


@router.get("/transcripts/{transcript_id}")
def api_get_transcript(transcript_id: int, request: Request) -> Dict[str, Any]:
    """获取指定转写记录的详情（包含 segments）。"""
    db_url = request.app.state.db_url
    data = get_transcript_by_id(db_url, transcript_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"transcript not found: {transcript_id}")
    return data


@router.delete("/transcripts/{transcript_id}")
def api_delete_transcript_complete(transcript_id: int, request: Request) -> Dict[str, Any]:
    """删除指定的转写记录及其对应的视频文件。
    该操作会同时删除视频文件和数据库记录，不可恢复。
    """
    logging.info(f"开始删除操作 - transcript_id: {transcript_id}")

    db_url = request.app.state.db_url
    static_dir: Path = request.app.state.static_dir

    logging.info(f"数据库连接: {db_url}")
    logging.info(f"静态目录: {static_dir}")

    # 检查转写记录是否存在
    transcript = get_transcript_by_id(db_url, transcript_id)
    if not transcript:
        logging.error(f"转写记录不存在: {transcript_id}")
        raise HTTPException(status_code=404, detail=f"transcript not found: {transcript_id}")

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
        success = delete_transcript(db_url, transcript_id)
        logging.info(f"数据库删除结果: {success}")

        if not success:
            logging.error(f"数据库删除失败: {transcript_id}")
            raise HTTPException(status_code=404, detail="转写记录不存在或已被删除")

        logging.info(f"已删除转写记录: {transcript_id}")

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
            "errors": errors if errors else None
        }

    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        logging.error(f"删除操作失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除操作失败: {str(e)}")