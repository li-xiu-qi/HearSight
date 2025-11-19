"""
测试下载进度获取
"""
import os
import sys
from pathlib import Path
from yt_dlp import YoutubeDL
import json
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_download_with_progress():
    """测试下载时获取进度信息"""
    
    url = "https://www.bilibili.com/video/BV113nizVEGt?spm_id_from=333.1007.tianma.6-1-19.click"
    out_dir = "downloads"
    
    os.makedirs(out_dir, exist_ok=True)
    
    # 用于存储进度信息的字典
    progress_data = {
        "status": None,
        "total_bytes": None,
        "downloaded_bytes": None,
        "progress_percentage": 0,
        "speed": None,
        "eta": None,
        "filename": None,
    }
    
    def progress_hook(d):
        """yt-dlp 的进度回调函数"""
        if d["status"] == "downloading":
            progress_data["status"] = "downloading"
            total = d.get("total_bytes", 0) or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            
            progress_data["total_bytes"] = total
            progress_data["downloaded_bytes"] = downloaded
            progress_data["filename"] = d.get("filename", "unknown")
            
            if total > 0:
                progress_data["progress_percentage"] = (downloaded / total) * 100
            else:
                progress_data["progress_percentage"] = 0
                
            progress_data["speed"] = d.get("speed")  # 下载速度（字节/秒）
            progress_data["eta"] = d.get("eta")      # 预计剩余时间（秒）
            
            # 打印进度信息
            speed_str = format_bytes(d.get("speed", 0)) if d.get("speed") else "N/A"
            eta_str = format_seconds(d.get("eta", 0)) if d.get("eta") else "N/A"
            
            print(f"[进度] {progress_data['progress_percentage']:.1f}% | "
                  f"已下载: {format_bytes(downloaded)} / {format_bytes(total)} | "
                  f"速度: {speed_str}/s | "
                  f"剩余: {eta_str}")
                  
        elif d["status"] == "finished":
            progress_data["status"] = "finished"
            print("\n[完成] 下载完成，开始处理文件...")
            
        elif d["status"] == "error":
            progress_data["status"] = "error"
            print(f"\n[错误] {d}")
    
    # yt-dlp 配置
    ydl_opts = {
        "format": "bv*+ba/best",
        "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": False,
        "overwrites": True,
        "windowsfilenames": True,
        "progress_hooks": [progress_hook],  # 添加进度回调
        "socket_timeout": 30,
        "retries": 3,
        "fragment_retries": 3,
        "concurrent_fragment_downloads": 1,
        "nopart": os.name == "nt",
    }
    
    print(f"开始下载: {url}")
    print(f"输出目录: {os.path.abspath(out_dir)}\n")
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            # 先获取视频信息
            print("[信息] 获取视频信息...")
            info = ydl.extract_info(url, download=True)
            
            # 下载完成后的结果
            print("\n" + "="*60)
            print("下载完成！")
            print("="*60)
            
            if isinstance(info, dict):
                print(f"视频标题: {info.get('title', 'N/A')}")
                print(f"视频ID: {info.get('id', 'N/A')}")
                print(f"时长: {format_seconds(info.get('duration', 0))}")
                print(f"上传者: {info.get('uploader', 'N/A')}")
                
                # 如果有文件路径
                if info.get('filepath'):
                    print(f"文件路径: {info.get('filepath')}")
                    file_size = os.path.getsize(info.get('filepath'))
                    print(f"文件大小: {format_bytes(file_size)}")
            
            print("\n进度统计:")
            print(json.dumps({
                "最终状态": progress_data["status"],
                "下载字节": progress_data["downloaded_bytes"],
                "总字节": progress_data["total_bytes"],
                "进度百分比": f"{progress_data['progress_percentage']:.1f}%",
            }, indent=2, ensure_ascii=False))
            
            return True
            
    except Exception as e:
        print(f"\n[错误] 下载失败: {str(e)}")
        return False


def format_bytes(bytes_val):
    """将字节转换为可读格式"""
    if bytes_val is None or bytes_val == 0:
        return "0 B"
    
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    
    return f"{bytes_val:.2f} TB"


def format_seconds(seconds):
    """将秒转换为可读格式"""
    if seconds is None or seconds == 0:
        return "0s"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


if __name__ == "__main__":
    success = test_download_with_progress()
    sys.exit(0 if success else 1)
