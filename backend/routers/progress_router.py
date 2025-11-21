"""下载和处理进度查询路由"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import redis
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing_extensions import TypedDict

from backend.config import settings


# 数据结构定义
class ProgressData(TypedDict, total=False):
    """进度数据结构"""

    status: str  # 任务状态
    stage: str  # 处理阶段
    progress_percent: float  # 进度百分比
    filename: str  # 文件名
    message: str  # 状态消息
    job_id: int  # 任务ID
    current_bytes: int  # 当前已处理的字节数
    total_bytes: int  # 总字节数
    speed: float  # 处理速度
    eta_seconds: Optional[int]  # 预计剩余时间
    timestamp: str  # 时间戳
    items: List[Dict[str, Any]]  # 结果项列表
    error: str  # 错误信息
    duplicate: bool  # 是否为重复任务
    original_job_id: int  # 原始任务ID


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["progress"])

# Redis连接，用于存储任务进度
# 优先使用 Celery 的 result backend（如配置），可通过 settings.celery_result_backend 修改
# 优先使用 Celery 配置中的 result backend（用于存放任务相关的元数据），
# 如果没有配置 result backend，再使用 broker 作为回退
redis_url_for_progress = settings.celery_result_backend or settings.celery_broker_url
redis_client = redis.Redis.from_url(redis_url_for_progress, decode_responses=True)
logger.info(f"Progress redis client using url: {redis_url_for_progress}")


def get_task_progress(job_id: int) -> ProgressData:
    """获取任务进度（包括下载和ASR阶段）"""
    key = f"task_progress:{job_id}"
    data = redis_client.get(key)
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            logger.error(f"解析任务进度数据失败 job_id={job_id}")
    
    return {
        "status": "idle",
        "stage": "waiting",
        "progress_percent": 0,
        "filename": "",
        "message": "等待处理",
    }


def set_task_progress(job_id: int, progress: ProgressData) -> bool:
    """设置任务进度"""
    key = f"task_progress:{job_id}"
    try:
        data = json.dumps(progress, ensure_ascii=False)
        # 输出redis连接信息用于调试
        try:
            conn_kwargs = getattr(redis_client.connection_pool, 'connection_kwargs', {})
            host = conn_kwargs.get('host') or conn_kwargs.get('address') or conn_kwargs.get('url') or 'unknown'
            port = conn_kwargs.get('port', 'unknown')
            db = conn_kwargs.get('db', 'unknown')
            logger.debug(f"Redis client connect: host={host}, port={port}, db={db}")
        except Exception:
            logger.debug("无法获取redis连接的详细信息")

        redis_client.setex(key, 86400, data)  # 设置24小时过期
        # 记录写入的值，以便调试
        try:
            read_back = redis_client.get(key)
            logger.info(f"写入Redis进度 key={key}, value={data}, readback={read_back}")
            # Publish progress update to pubsub channel so SSE / stream-all can push it
            try:
                redis_client.publish('progress_channel', data)
            except Exception:
                logger.debug('publish progress_channel failed')
        except Exception:
            logger.info(f"写入Redis进度 key={key}, value={data} (readback failed)")
        return True
    except Exception as e:
        logger.error(f"设置任务进度失败 job_id={job_id}: {e}")
        return False








async def generate_progress_events(job_id: int):
    """生成SSE进度事件流"""
    last_progress = None

    while True:
        try:
            current_progress = get_task_progress(job_id)

            # 只有当进度发生变化时才发送事件
            if current_progress != last_progress:
                # SSE格式: data: <json>\n\n
                data = json.dumps(current_progress, ensure_ascii=False)
                yield f"data: {data}\n\n"
                last_progress = current_progress.copy()

                # 如果任务已完成或失败，停止推送
                if current_progress.get("status") in ["completed", "success", "failed"]:
                    break

            # 每秒检查一次进度更新
            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"SSE进度推送错误 job_id={job_id}: {e}")
            error_data = {
                "status": "error",
                "stage": "connection_error",
                "progress_percent": 0,
                "message": "连接错误",
                "error": str(e),
                "job_id": job_id
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            break




@router.get("/progress/stream-all")
async def stream_all_progress():
    """SSE 推送全部进度事件（订阅 Redis pubsub channel `progress_channel`）

    客户端可订阅该路由来接收系统中所有任务的进度更新，从而替代轮询。
    """
    pubsub = redis_client.pubsub()
    pubsub.subscribe('progress_channel')

    async def event_generator():
        try:
            while True:
                message = pubsub.get_message(ignore_subscribe_messages=True)
                if message and message.get('type') == 'message':
                    yield f"data: {message.get('data')}\n\n"
                await asyncio.sleep(0.1)
        finally:
            try:
                pubsub.unsubscribe('progress_channel')
            except Exception:
                pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )
