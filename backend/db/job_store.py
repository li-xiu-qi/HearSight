# -*- coding: utf-8 -*-
"""任务存储模块，统一导出所有任务相关函数"""

from .job_base_store import get_job
from .job_status_store import update_job_status
from .job_result_store import finish_job_success, finish_job_failed, update_job_result