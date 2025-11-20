# -*- coding: utf-8 -*-
"""HearSight 应用入口"""

from __future__ import annotations

import sys
import os

# 添加项目根目录到 sys.path 以支持模块导入
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app import create_app
from backend.startup import initialize_app, get_backend_port

# 初始化应用
static_dir, db_url = initialize_app()

# 创建 FastAPI 应用
app = create_app(static_dir, db_url)

if __name__ == "__main__":
    import uvicorn

    port = get_backend_port()
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
