# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import get_config
from backend.db.sqlite_store import init_db, claim_next_pending_job, finish_job_success, finish_job_failed
from backend.download_video.download_bilibili import download_bilibili
from backend.audio2text.asr_sentence_segments import process as asr_process
from backend.routers.media import router as media_router
from backend.api.http.routes_asr import router as asr_router
from backend.api.http.routes_text import router as text_router
from backend.api.http.routes_chat import router as chat_router


APP_DIR = Path(__file__).parent.resolve()

cfg = get_config() or {}
app_datas = cfg.get("app_datas", {}) if isinstance(cfg, dict) else {}

# 读取配置（相对路径以 main.py 同级目录为基准）
download_video_path = Path(app_datas.get("download_video_path", "app_datas/download_videos"))
db_dir = Path(app_datas.get("db_path", "app_datas/db"))

if not download_video_path.is_absolute():
    download_video_path = (APP_DIR / download_video_path).resolve()
if not db_dir.is_absolute():
    db_dir = (APP_DIR / db_dir).resolve()

# 确保目录存在，并初始化数据库文件
download_video_path.mkdir(parents=True, exist_ok=True)
db_dir.mkdir(parents=True, exist_ok=True)
db_file = (db_dir / "app.sqlite3").resolve()
init_db(db_file)

# 创建应用
app = FastAPI(title="SmartMedia API")

# CORS（开发阶段放开）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态目录（下载的视频存放于此，前端通过 /static/xxx 访问）
app.mount("/static", StaticFiles(directory=str(download_video_path)), name="static")

# 注入全局状态，供路由读取
app.state.static_dir = download_video_path
app.state.db_path = db_file

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
    db_path: Path = app.state.db_path
    while True:
        job = claim_next_pending_job(db_path)
        if not job:
            time.sleep(1.0)
            continue
        job_id = int(job["id"])  # type: ignore
        url = str(job["url"])    # type: ignore
        try:
            # 读取当前任务的 result，用于阶段性恢复
            from backend.db.sqlite_store import get_job, update_job_result, save_transcript  # 局部导入避免循环
            info = get_job(db_path, job_id) or {}
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
                update_job_result(db_path, job_id, {
                    "media_path": media_path,
                    "basename": basename,
                    "static_url": f"/static/{basename}",
                })
            else:
                basename = Path(str(media_path)).name

            # Step B: ASR 阶段（若无 transcript_id，则执行识别与保存）
            if not res.get("transcript_id"):
                segs = asr_process(str(media_path))
                transcript_id = save_transcript(db_path, str(media_path), segs)
                res.update({"transcript_id": transcript_id})
                update_job_result(db_path, job_id, {"transcript_id": transcript_id})

            # Step C: 完成任务（写入完整结果）
            finish_job_success(db_path, job_id, res)
        except Exception as e:
            finish_job_failed(db_path, job_id, str(e))


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
        server_cfg = (cfg.get("server") or {})
        port = int(server_cfg.get("backend_port", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)