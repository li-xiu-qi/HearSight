# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from typing_extensions import TypedDict

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from backend.db.job_store import update_job_result_paths
from backend.db.job_store import create_job
from backend.db.transcript_crud import update_transcript_media_path
from backend.services.upload_service import (
    create_audio_placeholder,
    get_unique_filename,
)


# 数据结构定义
class UploadResult(TypedDict):
    """文件上传结果数据结构"""

    path: str  # 文件绝对路径
    basename: str  # 文件名
    static_url: str  # 静态文件URL
    size: int  # 文件大小（字节）
    is_audio: bool  # 是否为音频文件
    job_id: int  # 创建的任务ID
    placeholder_url: Optional[str]  # 音频文件的占位图URL（可选）


class UploadResponse(TypedDict):
    """文件上传响应数据结构"""

    success: bool  # 是否成功
    message: str  # 响应消息
    data: UploadResult  # 上传结果数据


class RenameFileRequest(TypedDict):
    """重命名文件请求数据结构"""

    old_filename: str  # 原始文件名
    new_filename: str  # 新文件名


class RenameFileResult(TypedDict, total=False):
    """重命名文件结果数据结构"""

    old_filename: str  # 原始文件名
    new_filename: str  # 新文件名
    static_url: str  # 静态文件URL
    placeholder_url: str  # 占位图URL（音频文件可选）


class RenameFileResponse(TypedDict):
    """重命名文件响应数据结构"""

    success: bool  # 是否成功
    message: str  # 响应消息
    data: RenameFileResult  # 重命名结果数据


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["upload"])

SUPPORTED_VIDEO_FORMATS = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}
SUPPORTED_AUDIO_FORMATS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB


@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
) -> JSONResponse:
    """上传视频或音频文件"""
    try:
        static_dir: Path = request.app.state.static_dir

        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名为空")

        file_ext = Path(file.filename).suffix.lower()

        if (
            file_ext not in SUPPORTED_VIDEO_FORMATS
            and file_ext not in SUPPORTED_AUDIO_FORMATS
        ):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {file_ext}。支持的视频格式: {', '.join(SUPPORTED_VIDEO_FORMATS)}，音频格式: {', '.join(SUPPORTED_AUDIO_FORMATS)}",
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{timestamp}_{Path(file.filename).stem}{file_ext}"
        safe_filename = get_unique_filename(static_dir, base_filename)
        file_path = static_dir / safe_filename

        file_size = 0
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"文件过大，最大支持 {MAX_FILE_SIZE // (1024*1024)}MB",
                    )
                buffer.write(chunk)

        logger.info(f"文件上传成功: {safe_filename} ({file_size / (1024*1024):.2f}MB)")

        result = {
            "path": str(file_path.resolve()),
            "basename": safe_filename,
            "static_url": f"/static/{safe_filename}",
            "size": file_size,
            "is_audio": file_ext in SUPPORTED_AUDIO_FORMATS,
        }

        if file_ext in SUPPORTED_AUDIO_FORMATS:
            placeholder_name = f"{Path(safe_filename).stem}_placeholder.jpg"
            placeholder_path = static_dir / placeholder_name
            create_audio_placeholder(placeholder_path)
            result["placeholder_url"] = f"/static/{placeholder_name}"

        db_url = request.app.state.db_url
        job_id = create_job(db_url, f"upload://{safe_filename}")
        logger.info(f"创建处理任务: job_id={job_id}, file={safe_filename}")

        result["job_id"] = job_id

        return JSONResponse(
            content={
                "success": True,
                "message": "文件上传成功,正在处理中",
                "data": result,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/upload/rename")
async def rename_file(
    request: Request,
    payload: RenameFileRequest,
) -> JSONResponse:
    """重命名已上传的文件"""
    try:
        old_filename = payload.get("old_filename")
        new_filename = payload.get("new_filename")

        if not old_filename or not new_filename:
            raise HTTPException(
                status_code=400, detail="old_filename 和 new_filename 都是必填项"
            )

        static_dir: Path = request.app.state.static_dir
        old_path = static_dir / old_filename

        if not old_path.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {old_filename}")

        file_ext = old_path.suffix.lower()
        new_file_ext = Path(new_filename).suffix.lower()

        if not new_file_ext:
            new_filename = f"{new_filename}{file_ext}"
        elif new_file_ext != file_ext:
            raise HTTPException(
                status_code=400, detail=f"不能更改文件扩展名，原扩展名: {file_ext}"
            )

        final_filename = get_unique_filename(static_dir, new_filename)
        new_path = static_dir / final_filename

        # 重命名文件
        old_path.rename(new_path)
        logger.info(f"文件重命名成功: {old_filename} -> {final_filename}")

        # 更新数据库中的media_path和job结果
        db_url = request.app.state.db_url
        old_media_path = str(old_path.resolve())
        new_media_path = str(new_path.resolve())

        try:
            # 更新transcripts表
            transcript_count = update_transcript_media_path(
                db_url, old_media_path, new_media_path
            )
            if transcript_count > 0:
                logger.info(f"已更新 {transcript_count} 条转写记录的media_path")

            # 更新jobs表的result字段
            job_count = update_job_result_paths(
                db_url, old_filename, final_filename, str(static_dir)
            )
            if job_count > 0:
                logger.info(f"已更新 {job_count} 个任务的result信息")
        except Exception as e:
            logger.warning(f"更新数据库失败: {e}")

        result = {
            "old_filename": old_filename,
            "new_filename": final_filename,
            "static_url": f"/static/{final_filename}",
        }

        is_audio = file_ext in SUPPORTED_AUDIO_FORMATS
        if is_audio:
            old_placeholder = static_dir / f"{old_path.stem}_placeholder.jpg"
            if old_placeholder.exists():
                new_placeholder = (
                    static_dir / f"{Path(final_filename).stem}_placeholder.jpg"
                )
                old_placeholder.rename(new_placeholder)
                result["placeholder_url"] = f"/static/{new_placeholder.name}"

        return JSONResponse(
            content={
                "success": True,
                "message": f"文件重命名成功{' (已自动调整为 ' + final_filename + ')' if final_filename != new_filename else ''}",
                "data": result,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件重命名失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件重命名失败: {str(e)}")
