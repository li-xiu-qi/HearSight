# -*- coding: utf-8 -*-
"""HearSight 应用入口"""

from __future__ import annotations

from backend.app import create_app
from backend.startup import initialize_app, get_backend_port
from backend.worker.job_worker import start_worker

# 初始化应用
static_dir, db_url = initialize_app()

# 创建 FastAPI 应用
app = create_app(static_dir, db_url)

# 启动后台 worker
start_worker(app, db_url)

if __name__ == "__main__":
    import uvicorn

    port = get_backend_port()
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)