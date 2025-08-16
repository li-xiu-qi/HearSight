import os
from yt_dlp import YoutubeDL




def download_bilibili(
    url: str,
    out_dir: str = "downloads",
    sessdata: str = None,
    playlist: bool = False,
    quality: str = "best",
    workers: int = 16,
) -> list[str]:
    """
    使用 yt-dlp 下载哔站视频，返回最终合并后的文件路径列表。

    参数：
    - url: 视频页或合集/分P链接
    - out_dir: 输出目录
    - sessdata: 你的登录 SESSDATA，用于解锁更高清晰度/限制内容
    - playlist: 是否下载合集中全部或分P（True 下载全部，False 仅当前）
    - quality: 清晰度/格式选择，默认 'best'；也可传自定义格式选择表达式
    - workers: 分片并发数，提高下载速度

    返回：
    - list[str]: 每个条目的最终输出文件完整路径（合并后）
    """
    os.makedirs(out_dir, exist_ok=True)

    # 选择格式：默认优先分离封装的最优视频+音频
    # 你也可以改成如 "bv[height<=1080]+ba/best" 来限 1080p
    fmt = "bv*+ba/best" if quality == "best" else quality

    # 仅在提供了 sessdata 时注入 Cookie 头
    http_headers = {"Cookie": f"SESSDATA={sessdata}"} if sessdata else None

    ydl_opts = {
        "format": fmt,
        "merge_output_format": "mp4",  # 合并容器为 mp4（若可行）
        # 加入分P序号与 B 站 cid，避免同名冲突；NA 置空
        "outtmpl": os.path.join(out_dir, "%(title)s [%(id)s][P%(playlist_index)02d][cid=%(cid)s].%(ext)s"),
        "outtmpl_na_placeholder": "",
        # 将 SESSDATA 以 Cookie 注入，通常即可访问大多数受限清晰度
        # 若为空则不设置该头
        **({"http_headers": http_headers} if http_headers else {}),
        "noplaylist": not playlist,
        "concurrent_fragment_downloads": workers,
        # 安静模式关闭以便看到进度；如需更安静可设 True
        "quiet": False,
        # 允许覆盖已存在同名文件，配合唯一命名更稳妥
        "overwrites": True,
        # Windows 文件名安全
        "windowsfilenames": True,
    }

    def _iter_entries(info):
        if not info:
            return
        # playlist 或 multi-video
        entries = info.get("entries") if isinstance(info, dict) else None
        if entries:
            for e in entries:
                yield from _iter_entries(e)
        else:
            yield info

    results: list[str] = []
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        for item in _iter_entries(info):
            # yt-dlp 在下载/后处理后会在 info 里填充最终文件路径
            fp = item.get("filepath") if isinstance(item, dict) else None
            if not fp:
                # 兼容兜底：根据模板推导文件名，并在需要时替换合并后的扩展名
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

