# -*- coding: utf-8 -*-
"""缩略图路由"""

from __future__ import annotations

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from backend.db.pg_store import get_transcript_by_id
from backend.services.thumbnail_service import generate_thumbnail
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["thumbnail"])


@router.get("/thumbnails/{transcript_id}")
async def get_thumbnail(
    transcript_id: int,
    start_time: float,
    end_time: float,
    width: int = 320,
    request: Request = None
) -> JSONResponse:
    """
    获取视频缩略图
    
    Args:
        transcript_id: 转写记录 ID
        start_time: 开始时间（毫秒）
        end_time: 结束时间（毫秒）
        width: 缩略图宽度（可选，默认 320）
        
    Returns:
        JSON 响应，包含 base64 编码的图片数据
        {
            "success": true,
            "data": "data:image/jpeg;base64,/9j/4AAQ..."
        }
    """
    try:
        # 获取数据库连接
        db_url = request.app.state.db_url
        
        # 获取转写记录
        transcript = get_transcript_by_id(db_url, transcript_id)
        if not transcript:
            raise HTTPException(status_code=404, detail=f"转写记录不存在: {transcript_id}")
        
        # 获取视频路径
        video_path = transcript.get("media_path")
        if not video_path:
            raise HTTPException(status_code=400, detail="转写记录中没有视频路径")
        
        logger.info(f"生成缩略图: transcript_id={transcript_id}, time={start_time}-{end_time}ms")
        
        # 生成缩略图
        thumbnail_data = generate_thumbnail(
            video_path=video_path,
            start_time_ms=start_time,
            end_time_ms=end_time,
            width=width
        )
        
        if thumbnail_data is None:
            raise HTTPException(status_code=500, detail="生成缩略图失败")
        
        return JSONResponse(content={
            "success": True,
            "data": thumbnail_data
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取缩略图失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取缩略图失败: {str(e)}")
