import os
from yt_dlp import YoutubeDL


def download_bilibili(
    url: str,
    out_dir: str = "downloads",
    sessdata: str = None,
    playlist: bool = False,
    quality: str = "best",
    workers: int = 16,
    use_nopart: bool | None = None,
    simple_filename: bool = True,
) -> list[str]:
    """
    bilibili 下载函数（基于 yt-dlp）。

    - 保留必要选项：输出目录、SESSDATA（可选）、是否下载 playlist、清晰度、并发片段数。
    - 在 Windows 上默认启用 nopart（直接写入最终文件名），可以通过参数覆盖。
    - 返回下载条目的最终文件路径列表（尝试从 info 中读取 filepath，否则用 prepare_filename 推断）。
    """

    # 确保输出目录存在
    os.makedirs(out_dir, exist_ok=True)

    # Windows 上默认启用 nopart（避免某些场景下 .part 重命名失败），非 Windows 则默认关闭
    if use_nopart is None:
        use_nopart = os.name == "nt"

    # 简单的格式选择：默认使用合并后最优视频+音频
    fmt = "bv*+ba/best" if quality == "best" else quality

    # 如果提供了 sessdata，则注入 Cookie 头以支持需要登录的清晰度/内容
    http_headers = {"Cookie": f"SESSDATA={sessdata}"} if sessdata else None

    # 输出模板：简单或带 id/分P 的详细模板
    if simple_filename:
        outtmpl = os.path.join(out_dir, "%(title)s.%(ext)s")
    else:
        outtmpl = os.path.join(out_dir, "%(title)s [%(id)s][P%(playlist_index)02d].%(ext)s")

    # 基本的 yt-dlp 参数，保持最小且清晰
    ydl_opts = {
        "format": fmt,
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
        "noplaylist": not playlist,
        "concurrent_fragment_downloads": workers,
        "quiet": False,
        "overwrites": True,
        "windowsfilenames": True,
    }

    if http_headers:
        ydl_opts["http_headers"] = http_headers
    if use_nopart:
        ydl_opts["nopart"] = True

    def _iter_entries(info):
        """Flatten info/entries 结构，yield 每个最终视频条目（单个或分P）。"""
        if not info:
            return
        entries = info.get("entries") if isinstance(info, dict) else None
        if entries:
            for e in entries:
                yield from _iter_entries(e)
        else:
            yield info

    results: list[str] = []
    with YoutubeDL(ydl_opts) as ydl:
        # 执行下载；yt-dlp 会在 info 中填充后处理结果
        info = ydl.extract_info(url, download=True)

        for item in _iter_entries(info):
            # 优先使用 yt-dlp 填充的 filepath
            fp = item.get("filepath") if isinstance(item, dict) else None
            if not fp:
                # 若没有，则用 prepare_filename 推断最终文件名（并考虑 merge_output_format）
                try:
                    guessed = ydl.prepare_filename(item)
                    merge_fmt = ydl.params.get("merge_output_format")
                    if merge_fmt:
                        base, _ = os.path.splitext(guessed)
                        guessed = f"{base}.{merge_fmt}"
                    fp = guessed
                except Exception:
                    fp = None

            if fp:
                results.append(fp)

    return results

