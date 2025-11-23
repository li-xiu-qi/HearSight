# -*- coding: utf-8 -*-
"""Celery异步任务定义 - 模块化版本"""

# 导入分解后的任务模块
from .process_job_task import process_job_task

__all__ = ["process_job_task"]