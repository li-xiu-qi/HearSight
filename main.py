# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import get_config, load_config
from backend.db.pg_store import init_db, claim_next_pending_job, finish_job_success, finish_job_failed
from backend.utils.vedio_utils.download_video.download_bilibili import download_bilibili
from backend.audio2text.asr_sentence_segments import process as asr_process
from backend.routers.media import router as media_router
from backend.api.http.routes_asr import router as asr_router
from backend.api.http.routes_text import router as text_router
from backend.api.http.routes_chat import router as chat_router


APP_DIR = Path(__file__).parent.resolve()

cfg = get_config()
# 同时读取原始的 .env dict（若有更复杂的 app_datas 配置可以放在这里）
raw_cfg = load_config()
app_datas = raw_cfg.get("app_datas", {}) if isinstance(raw_cfg, dict) else {}

# 读取配置（相对路径以 main.py 同级目录为基准）
download_video_path = Path(app_datas.get("download_video_path", "app_datas/download_videos"))

if not download_video_path.is_absolute():
    download_video_path = (APP_DIR / download_video_path).resolve()

# 确保目录存在，并初始化数据库文件
download_video_path.mkdir(parents=True, exist_ok=True)
db_url = os.environ.get("POSTGRES_DSN") or os.environ.get("DATABASE_URL") or None
init_db(db_url)

# 创建应用
app = FastAPI(title="SmartMedia API")

# CORS（开发阶段放开）
# 支持通过环境变量在 docker 部署时显式设置允许来源，例如 FRONTEND_HOST/FRONTEND_PORT 或 ALLOW_ORIGINS
allow_origins_env = os.environ.get('ALLOW_ORIGINS')
if allow_origins_env:
    # 支持逗号分隔的 origin 列表
    allow_origins = [s.strip() for s in allow_origins_env.split(',') if s.strip()]
else:
    frontend_host = os.environ.get('FRONTEND_HOST')
    frontend_port = os.environ.get('FRONTEND_PORT')
    if frontend_host and frontend_port:
        allow_origins = [f"http://{frontend_host}:{frontend_port}"]
    else:
        # 默认开放，便于开发（如需生产收紧，请通过 ALLOW_ORIGINS 设置）
        allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态目录（下载的视频存放于此，前端通过 /static/xxx 访问）
app.mount("/static", StaticFiles(directory=str(download_video_path)), name="static")
app.state.static_dir = download_video_path
app.state.db_url = db_url

# 注册路由
app.include_router(media_router)
app.include_router(asr_router)
app.include_router(text_router)
app.include_router(chat_router)

# 启动后台worker：简单串行处理下载+ASR，避免阻塞请求线程
def _job_worker(app: FastAPI) -> None:
    import time
    from pathlib import Path
    static_dir: Path = app.state.static_dir
    while True:
        job = claim_next_pending_job(db_url)
        if not job:
            time.sleep(1.0)
            continue
        job_id = int(job["id"])  
        url = str(job["url"])   
        try:
            # 读取当前任务的 result，用于阶段性恢复
            from backend.db.pg_store import get_job, update_job_result, save_transcript  # 局部导入避免循环
            info = get_job(db_url, job_id) or {}
            res = dict(info.get("result") or {})

            # Step A: 下载阶段（若无 media_path 或文件不存在，则执行下载并写入进度）
            media_path = res.get("media_path")
            if not media_path or not Path(str(media_path)).exists():
                files = download_bilibili(url=url, out_dir=str(static_dir), use_nopart=True, simple_filename=True)
                if not files:
                    raise RuntimeError("下载结果为空")
                media_path = str(Path(files[0]).resolve())
                basename = Path(media_path).name
                res.update({
                    "media_path": media_path,
                    "basename": basename,
                    "static_url": f"/static/{basename}",
                })
                update_job_result(db_url, job_id, {
                    "media_path": media_path,
                    "basename": basename,
                    "static_url": f"/static/{basename}",
                })
            else:
                basename = Path(str(media_path)).name

            # Step B: ASR 阶段（若无 transcript_id，则执行识别与保存）
            if not res.get("transcript_id"):
                segs = asr_process(str(media_path))
                transcript_id = save_transcript(db_url, str(media_path), segs)
                res.update({"transcript_id": transcript_id})
                update_job_result(db_url, job_id, {"transcript_id": transcript_id})

            # Step C: 完成任务（写入完整结果）
            finish_job_success(db_url, job_id, res)
        except Exception as e:
            finish_job_failed(db_url, job_id, str(e))


def _start_worker(app: FastAPI) -> None:
    import threading
    t = threading.Thread(target=_job_worker, args=(app,), daemon=True)
    t.start()

_start_worker(app)

if __name__ == "__main__":
    import uvicorn
    # 启动端口优先级：环境变量 PORT > config.yaml(server.backend_port) > 8000
    env_port = os.environ.get("PORT")
    if env_port is not None:
        port = int(env_port)
    else:
        # 优先使用 pydantic Config 的 BACKEND_PORT 字段，其次回退到 8000
        port = int(cfg.BACKEND_PORT) if getattr(cfg, "BACKEND_PORT", None) else 8000
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)