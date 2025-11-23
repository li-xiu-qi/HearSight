# -*- coding: utf-8 -*-
"""ASR处理阶段"""

from typing import Dict, Any, List, Optional

from backend.audio2text.asr_sentence_segments import process as asr_process
from backend.db.transcript_crud import save_transcript
from backend.db.job_store import update_job_result
from .progress_utils import update_task_progress, create_progress_info


def handle_asr_stage(
    audio_path: str,
    video_path: Optional[str],
    media_type: str,
    audio_basename: str,
    job_id: int,
    set_task_progress_func,
    redis_client,
    db_url: Optional[str] = None
) -> tuple[int, List[Dict[str, Any]]]:
    """处理ASR阶段

    Returns:
        (transcript_id, segments)
    """
    # ASR预处理进度
    progress_info = create_progress_info(
        job_id, "processing", "asr_preprocessing", 5,
        filename=audio_basename, message="正在准备语音识别..."
    )
    update_task_progress(set_task_progress_func, redis_client, job_id, progress_info)

    # ASR识别进度
    progress_info = create_progress_info(
        job_id, "processing", "asr_recognizing", 10,
        filename=audio_basename, message="正在进行语音识别,请稍候..."
    )
    update_task_progress(set_task_progress_func, redis_client, job_id, progress_info)

    # 执行ASR
    segs = asr_process(audio_path)

    # ASR后处理进度
    progress_info = create_progress_info(
        job_id, "processing", "asr_postprocessing", 80,
        filename=audio_basename, message="语音识别完成,正在处理结果..."
    )
    update_task_progress(set_task_progress_func, redis_client, job_id, progress_info)

    # 保存转录结果进度
    progress_info = create_progress_info(
        job_id, "processing", "saving_transcript", 90,
        filename=audio_basename, message="正在保存转录结果..."
    )
    update_task_progress(set_task_progress_func, redis_client, job_id, progress_info)

    # 保存转录结果
    transcript_id = save_transcript(db_url, audio_path, segs, media_type, video_path=video_path)

    # 更新任务结果
    update_job_result(db_url, job_id, {"transcript_id": transcript_id, "media_type": media_type})

    # ASR完成进度
    progress_info = create_progress_info(
        job_id, "completed", "asr", 100,
        filename=audio_basename, message="语音识别完成"
    )
    update_task_progress(set_task_progress_func, redis_client, job_id, progress_info)

    return transcript_id, segs