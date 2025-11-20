"""ASR 路由模块

提供语音识别相关的 API 接口，支持本地和云端两种模式。

支持的三种输入方式：
- /transcribe/bytes: 本地字节流识别（本地模式）
- /transcribe/url: URL 直接识别（云端模式）
- /transcribe/upload: 文件上传到 Supabase 后识别（云端模式）
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from config import settings
from services.asr_service import ASRService

router = APIRouter(prefix="/asr", tags=["ASR"])


@router.post("/transcribe/bytes")
async def transcribe_from_bytes(file: UploadFile = File(...)) -> JSONResponse:
    """从音频字节流进行语音识别（本地模式）

    直接上传音频文件，使用本地 FunASR 模型进行识别。
    适合对隐私要求高、延迟敏感的场景。

    Args:
        file: 音频文件（支持 wav, mp3, m4a, flac, ogg）

    Returns:
        识别结果的 JSON 响应
    """
    # 文件格式校验
    if not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".flac", ".ogg")):
        raise HTTPException(
            status_code=400,
            detail="不支持的文件格式。支持的格式：wav, mp3, m4a, flac, ogg",
        )

    try:
        audio_data = await file.read()
        result = await ASRService.transcribe_from_bytes(audio_data, file.filename)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音识别失败: {str(e)}")


@router.post("/transcribe/url")
async def transcribe_from_url(url: str = Form(...)) -> JSONResponse:
    """从音频 URL 进行语音识别（云端模式）

    提供音频文件 URL，通过 DashScope 云端 API 进行识别。
    需要网络连接，适合处理远程音频文件。

    Args:
        url: 音频文件 URL

    Returns:
        识别结果的 JSON 响应
    """
    # URL 基本格式校验
    if not url or not isinstance(url, str):
        raise HTTPException(status_code=400, detail="必须提供有效的 URL")

    if not url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="URL 必须以 http:// 或 https:// 开头")

    # 检查是否为常见的音频文件 URL（可选校验）
    audio_extensions = ('.wav', '.mp3', '.m4a', '.flac', '.ogg')
    if not any(url.lower().endswith(ext) for ext in audio_extensions):
        # 不强制要求，但给出警告
        pass

    try:
        result = await ASRService.transcribe_from_url(url)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音识别失败: {str(e)}")


@router.post("/transcribe/upload")
async def transcribe_from_file_with_upload(file: UploadFile = File(...)) -> JSONResponse:
    """上传文件到 Supabase 后进行语音识别（云端模式）

    先将音频文件上传到 Supabase 云存储获得公开 URL，
    然后通过 DashScope 云端 API 进行语音识别。
    适合需要文件存储和云端处理的场景。

    Args:
        file: 音频文件（支持 wav, mp3, m4a, flac, ogg）

    Returns:
        识别结果的 JSON 响应，包含上传的 URL 信息
    """
    # 文件格式校验
    if not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".flac", ".ogg")):
        raise HTTPException(
            status_code=400,
            detail="不支持的文件格式。支持的格式：wav, mp3, m4a, flac, ogg",
        )

    try:
        audio_data = await file.read()
        result = await ASRService.transcribe_from_file_with_upload(audio_data, file.filename)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音识别失败: {str(e)}")


