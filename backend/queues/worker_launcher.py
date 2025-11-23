# -*- coding: utf-8 -*-
"""Celery worker启动脚本"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# 获取项目根目录
if os.path.exists("/app"):
    project_root = "/app"
else:
    project_root = str(Path(__file__).parent.parent.parent)

# 添加项目根目录到 sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 加载环境变量
from dotenv import load_dotenv
env_file = Path(project_root) / "backend" / ".env"
if env_file.exists():
    load_dotenv(env_file)

# 导入Celery应用
from backend.config import create_celery_app

def main():
    """启动Celery worker"""
    # 初始化应用组件
    from backend.startup import initialize_llm_router, initialize_embedding_router
    initialize_llm_router()
    initialize_embedding_router()
    
    # 从环境变量读取worker配置
    concurrency = int(os.getenv("CELERY_WORKER_CONCURRENCY", "4"))
    loglevel = os.getenv("CELERY_LOG_LEVEL", "info")

    print(f"启动Celery worker，并发数: {concurrency}, 日志级别: {loglevel}")
    from backend.config import settings
    print(f"Broker: {os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')}")
    print(f"Result backend: {getattr(settings, 'celery_result_backend', 'redis://localhost:6379/1')}")

    # 创建并启动worker
    celery_app = create_celery_app()
    celery_app.worker_main([
        "worker",
        "--loglevel", loglevel,
        "--concurrency", str(concurrency),
        "--pool", "solo",
        "--time-limit", "3600",
        "--soft-time-limit", "3300",
    ])

if __name__ == "__main__":
    main()
