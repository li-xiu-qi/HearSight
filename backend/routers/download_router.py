# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from backend.utils.vedio_utils.download_video.download_bilibili import download_bilibili

router = APIRouter(prefix="/api", tags=["download"])


@router.post("/download")
def api_download(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    """下载视频文件"""
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    static_dir: Path = request.app.state.static_dir
    out_dir = payload.get("out_dir") or str(static_dir)
    sessdata = payload.get("sessdata")
    playlist = bool(payload.get("playlist", False))
    quality = payload.get("quality", "best")
    workers = int(payload.get("workers", 16))

    files = download_bilibili(
        url=url,
        out_dir=out_dir,
        sessdata=str(sessdata) if sessdata else "",
        playlist=playlist,
        quality=quality,
        workers=workers,
        use_nopart=True,
        simple_filename=True,
    )

    items: List[Dict[str, Any]] = []
    for fp in files:
        p = Path(fp)
        # 只暴露静态访问路径
        items.append({
            "path": str(p.resolve()),
            "basename": p.name,
            "static_url": f"/static/{p.name}",
        })

    return {"items": items}