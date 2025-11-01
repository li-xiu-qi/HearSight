# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import requests
from tenacity import stop_after_attempt, wait_exponential, retry_if_exception, before_log

logger = logging.getLogger(__name__)


def on_retry_error(retry_state):
    """记录 tenacity 重试错误详情。"""
    exception = retry_state.outcome.exception()
    logger.warning(f"重试 {retry_state.fn.__name__}，原因：{type(exception).__name__}: {exception}，尝试次数：{retry_state.attempt_number}")


def should_retry(exception):
    """判定是否需要重试。"""
    if isinstance(exception, (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError)):
        return True
    if isinstance(exception, requests.HTTPError):
        # 仅对硅基流动 API 的 429 进行重试
        if exception.response is not None and exception.response.status_code == 429 and 'siliconflow' in str(exception.response.url):
            return True
        return False
    return False

__all__ = [
    "should_retry",
    "on_retry_error",
    "before_log",
    "stop_after_attempt",
    "wait_exponential",
    "retry_if_exception",
]
