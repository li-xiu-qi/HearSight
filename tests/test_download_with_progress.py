#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试支持进度反馈的下载函数"""

import sys
import json
from pathlib import Path
import time
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from backend.utils.vedio_utils.download_video.download_with_progress import (
        download_bilibili_with_progress,
        ProgressInfo,
    )
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保项目结构正确")
    sys.exit(1)


def _format_bytes(b):
    """格式化字节"""
    for unit in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.2f} {unit}"
        b /= 1024
    return f"{b:.2f} TB"


def _format_time(s):
    """格式化时间"""
    if s is None:
        return "N/A"
    if s < 60:
        return f"{s}s"
    elif s < 3600:
        return f"{s // 60}m {s % 60}s"
    else:
        return f"{s // 3600}h {(s % 3600) // 60}m"


def progress_callback(info: ProgressInfo) -> None:
    """进度回调函数"""
    status = info["status"]
    percent = info["progress_percent"]
    downloaded = info["downloaded_bytes"]
    total = info["total_bytes"]
    speed = info["speed"]
    eta = info["eta_seconds"]

    if status == "downloading":
        downloaded_fmt = _format_bytes(downloaded)
        total_fmt = _format_bytes(total)
        speed_fmt = _format_bytes(speed)
        eta_fmt = _format_time(eta)

        print(
            f"[进度] {percent:5.1f}% | 已下载: {downloaded_fmt:>12} / {total_fmt:>12} | 速度: {speed_fmt:>10}/s | 剩余: {eta_fmt:>8}",
            end="\r",
        )
    elif status == "finished":
        print("\n[完成] 下载完成！")
    elif status == "error":
        print("\n[错误] 下载失败")


def main():
    url = "https://www.bilibili.com/video/BV113nizVEGt?spm_id_from=333.1007.tianma.6-1-19.click"
    out_dir = "downloads"

    print(f"开始下载: {url}")
    print(f"输出目录: {Path(out_dir).resolve()}")
    print()

    try:
        files = download_bilibili_with_progress(
            url=url,
            out_dir=out_dir,
            progress_callback=progress_callback,
            simple_filename=True,
        )

        print("\n" + "=" * 60)
        print("下载成功！")
        print("=" * 60)
        print(f"下载的文件数: {len(files)}")
        for fp in files:
            p = Path(fp)
            size_mb = p.stat().st_size / (1024 * 1024)
            print(f"  - {p.name} ({size_mb:.2f} MB)")

    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
