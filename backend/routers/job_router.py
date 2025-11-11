# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from fastapi import APIRouter, HTTPException, Request

from backend.db.job_store import create_job, get_job, list_jobs


# 数据结构定义
class CreateJobRequest(TypedDict):
    """创建任务请求数据结构"""

    url: str  # 任务URL


class CreateJobResponse(TypedDict):
    """创建任务响应数据结构"""

    job_id: int  # 创建的任务ID


class JobData(TypedDict, total=False):
    """任务数据结构"""

    id: int  # 任务ID
    url: str  # 任务URL
    status: str  # 任务状态
    created_at: str  # 创建时间
    started_at: Optional[str]  # 开始时间
    finished_at: Optional[str]  # 完成时间
    result: Optional[Dict[str, Any]]  # 任务结果
    error: Optional[str]  # 错误信息


class GetJobResponse(JobData):
    """获取任务响应数据结构"""

    pass


class ListJobsQueryParams(TypedDict, total=False):
    """列出任务查询参数"""

    status: str  # 任务状态筛选
    limit: int  # 返回数量限制
    offset: int  # 偏移量


class ListJobsResponse(TypedDict):
    """列出任务响应数据结构"""

    items: List[JobData]  # 任务列表


router = APIRouter(prefix="/api", tags=["jobs"])


@router.post("/jobs")
def api_create_job(payload: CreateJobRequest, request: Request) -> CreateJobResponse:
    """创建新的处理任务"""
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    db_url = request.app.state.db_url
    job_id = create_job(db_url, str(url))
    return {"job_id": job_id}


@router.get("/jobs/{job_id}")
def api_get_job(job_id: int, request: Request) -> GetJobResponse:
    """获取指定任务的详情"""
    db_url = request.app.state.db_url
    data = get_job(db_url, int(job_id))
    if not data:
        raise HTTPException(status_code=404, detail=f"job not found: {job_id}")
    return data


@router.get("/jobs")
def api_list_jobs(
    request: Request, status: str | None = None, limit: int = 50, offset: int = 0
) -> ListJobsResponse:
    """列出任务队列，支持按状态筛选（downloading/processing/success/failed）。
    返回: { items: [{id, url, status, created_at, started_at, finished_at, result, error}] }
    """
    db_url = request.app.state.db_url
    items = list_jobs(db_url, status=status, limit=limit, offset=offset)
    return {"items": items}
