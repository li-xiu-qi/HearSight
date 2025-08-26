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
    simple_filename: bool = False,
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

    备注：在 Windows 上如果出现类似 "[WinError 32] 另一个程序正在使用此文件" 的重命名失败，可以传入
    `use_nopart=True` 来禁用下载时的临时 .part 文件（直接写入最终文件名），这样可以避免 yt-dlp 在尝试将
    .part 重命名为最终文件时被其他进程锁定。但禁用 .part 会在下载被中断时留下不完整的目标文件，按需使用。

    simple_filename: 如果为 True，则使用更简洁的输出模板，仅包含标题和扩展名：
        "%(title)s.%(ext)s"
    这会去掉自动添加的 BV id、cid、分P 标记等，用于对文件名更友好的展示，但会增加同名冲突的风险。
    """
    os.makedirs(out_dir, exist_ok=True)

    # 如果调用方没有显式设置 use_nopart，则在 Windows 上自动启用以避免 .part 重命名被系统锁定
    if use_nopart is None:
        use_nopart = (os.name == "nt")

    # 运行时打印当前设置，方便排查（uvicorn 控制台可见）
    print(f"download_bilibili: use_nopart={use_nopart}, out_dir={out_dir}")

    # 选择格式：默认优先分离封装的最优视频+音频
    # 你也可以改成如 "bv[height<=1080]+ba/best" 来限 1080p
    fmt = "bv*+ba/best" if quality == "best" else quality

    # 仅在提供了 sessdata 时注入 Cookie 头
    http_headers = {"Cookie": f"SESSDATA={sessdata}"} if sessdata else None

    # 输出模板候选：simple 模式和详细模式
    simple_template = os.path.join(out_dir, "%(title)s.%(ext)s")
    detailed_template = os.path.join(out_dir, "%(title)s [%(id)s][P%(playlist_index)02d][cid=%(cid)s].%(ext)s")

    # 如果用户要求简单文件名，先做一次 probe（download=False）来准备每个条目的文件名并检查是否已存在；
    # 若存在冲突则回退到详细模板，避免覆盖已存在文件。
    if simple_filename:
        probe_opts = {
            "outtmpl": simple_template,
            "merge_output_format": "mp4",
            "outtmpl_na_placeholder": "",
            "windowsfilenames": True,
            # 安静一些，probe 不需要太多输出
            "quiet": True,
        }
        try:
            from yt_dlp import YoutubeDL as _ProbeYDL

            with _ProbeYDL(probe_opts) as probe_ydl:
                info_probe = probe_ydl.extract_info(url, download=False)

                def _iter_entries_probe(info):
                    if not info:
                        return
                    entries = info.get("entries") if isinstance(info, dict) else None
                    if entries:
                        for e in entries:
                            yield from _iter_entries_probe(e)
                    else:
                        yield info

                conflict = False
                for item in _iter_entries_probe(info_probe):
                    try:
                        candidate = probe_ydl.prepare_filename(item)
                    except Exception:
                        # 如果 prepare_filename 失败，则保守地认为可能冲突，回退到详细模板
                        conflict = True
                        break
                    # 如果文件已存在则视为冲突
                    if os.path.exists(candidate):
                        conflict = True
                        break

                outtmpl_template = detailed_template if conflict else simple_template
        except Exception:
            # probe 失败时保守回退到详细模板以避免覆盖
            outtmpl_template = detailed_template
    else:
        outtmpl_template = detailed_template

    ydl_opts = {
        "format": fmt,
        "merge_output_format": "mp4",  # 合并容器为 mp4（若可行）
        # 加入分P序号与 B 站 cid，避免同名冲突；NA 置空
        "outtmpl": outtmpl_template,
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
    # 在 Windows 上如果其他进程可能会立即打开文件导致重命名失败，可禁用 .part 临时文件
    # 传入 use_nopart=True 将直接写入最终文件名，避免在重命名时被系统锁定
    **({"nopart": True} if use_nopart else {}),
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

