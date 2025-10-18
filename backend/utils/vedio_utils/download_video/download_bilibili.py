import os
import glob
import shutil
from yt_dlp import YoutubeDL
import logging
from typing import Optional

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _clean_temp_files(out_dir: str, title: str):
    """清理可能存在的临时文件"""
    try:
        # 查找可能的临时文件
        temp_patterns = [
            os.path.join(out_dir, f"{title}.*.part"),
            os.path.join(out_dir, f"{title}.*.tmp"),
            os.path.join(out_dir, f"{title}.*.part-Frag*"),
            os.path.join(out_dir, f"{title}.*.temp.*"),
        ]
        
        for pattern in temp_patterns:
            for temp_file in glob.glob(pattern):
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.info(f"已清理临时文件: {temp_file}")
    except Exception as e:
        logger.warning(f"清理临时文件时出错: {e}")


def download_bilibili(
    url: str,
    out_dir: str = "downloads",
    sessdata: Optional[str] = None,
    playlist: bool = False,
    quality: str = "best",
    workers: int = 1,  # 改为1，禁用多线程下载
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

    # Windows 上默认启用 nopart（避免某些场景下 .part 重认名失败），非 Windows 则默认关闭
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
        "concurrent_fragment_downloads": workers,  # 使用传入的workers参数
        "quiet": False,
        "overwrites": True,  # 允许覆盖已存在的文件
        "windowsfilenames": True,
        # 添加重试机制
        "retries": 3,
        "fragment_retries": 3,
        "skip_unavailable_fragments": True,
        # 解决HTTP 416错误的配置
        "continuedl": True,  # 继续部分下载
        "noresizebuffer": True,  # 不调整缓冲区大小
        # 当出现文件访问错误时重试
        "file_access_retries": 3,
        # 网络超时设置
        "socket_timeout": 30,
        "sleep_interval": 1,
        "max_sleep_interval": 5,
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
    try:
        with YoutubeDL(ydl_opts) as ydl:
            # 获取视频标题用于清理临时文件
            try:
                info_dict = ydl.extract_info(url, download=False)
                title = info_dict.get('title', 'unknown') if isinstance(info_dict, dict) else 'unknown'
                # 清理可能存在的临时文件
                _clean_temp_files(out_dir, title)
            except Exception as e:
                logger.warning(f"获取视频信息时出错: {e}")
            
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
    except Exception as e:
        logger.error(f"下载过程中发生错误: {str(e)}")
        raise e

    return results