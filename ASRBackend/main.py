"""HearSight ASR Backend

基于 FastAPI 构建的语音识别后端服务，提供音频转文本功能。
"""

from __future__ import annotations

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from ASRBackend.config import settings
    from ASRBackend.routers.asr_router import router as asr_router
except ImportError:
    # 相对导入（开发环境备用）
    from .config import settings
    from .routers.asr_router import router as asr_router

app = FastAPI(title=settings.app_name)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(asr_router)


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "ASR Backend"}


def main():
    """主启动函数"""
    print("=" * 60)
    print("HearSight ASR Backend")
    print("=" * 60)

    # 验证配置
    try:
        settings.validate_config()
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        import sys

        sys.exit(1)

    # 显示运行模式信息
    mode = settings.asr_mode
    if settings.is_local_mode():
        print(f"✓ 运行模式: 本地 (local)")
        print(f"  - 模型: {settings.local_model_name}")
        print(f"  - VAD 模型: {settings.local_vad_model}")
        print(f"  - 标点模型: {settings.local_punc_model}")
        print(f"  - 支持: 文件上传、URL")
        print(f"  - 特点: 完全离线，但需要大量空间和计算资源")
    else:
        print(f"✓ 运行模式: 云端 (cloud)")
        print(f"  - 提供商: DashScope (阿里云)")
        print(f"  - 模型: {settings.dashscope_model}")
        print(f"  - 语言提示: {settings.dashscope_language_hints}")
        print(f"  - 支持: URL 转录")
        print(f"  - 特点: 轻量级，支持多语言")

    print(f"✓ 调试模式: {'开启' if settings.debug else '关闭'}")
    print("=" * 60)
    print(f"启动服务器: http://0.0.0.0:{settings.port}")
    print("=" * 60)


if __name__ == "__main__":
    main()
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=settings.port,reload=True)
