# -*- coding: utf-8 -*-
"""下载和上传处理阶段"""

from pathlib import Path
from typing import Dict, Any, Optional

from backend.media_processing.upload_handler import process_uploaded_file
from backend.media_processing import MediaDownloaderFactory
from backend.db.job_store import update_job_result, update_job_status
from .progress_utils import update_task_progress, create_progress_info


def handle_download_stage(
    url: str,
    static_path: Path,
    job_id: int,
    set_task_progress_func,
    redis_client,
    db_url: Optional[str] = None
) -> Dict[str, Any]:
    """处理下载/上传阶段

    Returns:
        包含 audio_path, video_path, media_type, audio_basename 等信息的字典
    """
    result_data = {}

    # 检查是否是上传的文件
    if url.startswith("upload://"):
        return handle_upload_file(url, static_path, job_id, set_task_progress_func, redis_client, db_url)
    else:
        return handle_download_url(url, static_path, job_id, set_task_progress_func, redis_client, db_url)


def handle_upload_file(
    url: str,
    static_path: Path,
    job_id: int,
    set_task_progress_func,
    redis_client,
    db_url: Optional[str] = None
) -> Dict[str, Any]:
    """处理上传文件"""
    basename = url.replace("upload://", "")
    file_path = str((static_path / basename).resolve())

    if not Path(file_path).exists():
        raise RuntimeError(f"上传文件不存在: {file_path}")

    # 上传处理进度
    progress_info = create_progress_info(
        job_id, "processing", "upload_processing", 10,
        filename=basename, message="正在处理上传的文件..."
    )
    update_task_progress(set_task_progress_func, redis_client, job_id, progress_info)

    # 处理上传文件
    result = process_uploaded_file(file_path, str(static_path))
    if not result.success:
        raise RuntimeError(f"处理上传文件失败: {result.error_message}")

    # 完成进度
    progress_info = create_progress_info(
        job_id, "ready", "upload", 100,
        filename=basename, message="文件已上传并处理完成,准备进行语音识别"
    )
    update_task_progress(set_task_progress_func, redis_client, job_id, progress_info)

    update_data = {
        "audio_path": result.audio_path,
        "video_path": result.video_path,
        "basename": basename,
        "static_url": f"/static/{basename}",
        "source": "upload",
        "media_type": result.media_type,
    }

    update_job_result(db_url, job_id, update_data)

    return {
        "audio_path": result.audio_path,
        "video_path": result.video_path,
        "media_type": result.media_type,
        "audio_basename": basename,
        **update_data
    }


def handle_download_url(
    url: str,
    static_path: Path,
    job_id: int,
    set_task_progress_func,
    redis_client,
    db_url: Optional[str] = None
) -> Dict[str, Any]:
    """处理URL下载"""
    # 开始下载进度
    progress_info = create_progress_info(
        job_id, "pending", "download_start", 0,
        message="准备开始下载..."
    )
    update_task_progress(set_task_progress_func, redis_client, job_id, progress_info)

    update_job_status(db_url, job_id, "pending")

    def on_progress(info: Dict) -> None:
        """下载进度回调"""
        progress_info = create_progress_info(
            job_id,
            info.get("status", "downloading"),
            "download",
            info.get("progress_percent", 0),
            filename=info.get("filename", ""),
            current_bytes=info.get("downloaded_bytes", 0),
            total_bytes=info.get("total_bytes", 0),
            speed=info.get("speed", 0),
            eta_seconds=info.get("eta_seconds", 0)
        )
        update_task_progress(set_task_progress_func, redis_client, job_id, progress_info)

    factory = MediaDownloaderFactory(output_dir=str(static_path))
    result = factory.download(url, progress_callback=on_progress)
    if not result.success:
        raise RuntimeError(f"下载失败: {result.error_message}")

    # 处理结果
    audio_path = str(Path(result.audio_path).resolve()) if result.audio_path else None
    video_path = str(Path(result.video_path).resolve()) if result.video_path else None

    if not audio_path:
        raise RuntimeError("下载结果中没有音频文件")

    media_type = result.media_type or "audio"
    audio_basename = Path(audio_path).name

    # 下载完成进度
    progress_info = create_progress_info(
        job_id, "ready", "download", 100,
        filename=audio_basename, message="下载完成,准备进行语音识别"
    )
    update_task_progress(set_task_progress_func, redis_client, job_id, progress_info)

    update_data = {
        "audio_path": audio_path,
        "basename": audio_basename,
        "media_type": media_type,
        "source": "download"
    }
    if video_path:
        update_data["video_path"] = video_path
        update_data["static_url"] = f"/static/{Path(video_path).name}"
    else:
        update_data["static_url"] = f"/static/{audio_basename}"

    update_job_result(db_url, job_id, update_data)

    return {
        "audio_path": audio_path,
        "video_path": video_path,
        "media_type": media_type,
        "audio_basename": audio_basename,
        **update_data
    }